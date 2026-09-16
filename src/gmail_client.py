"""
Gmail MCP Server — gmail_client.py
Typed wrapper around the Google Gmail API.
"""

import os
import base64
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from src.auth import get_credentials

logger = logging.getLogger(__name__)

MAX_RESULTS = int(os.getenv("MAX_RESULTS", "20"))


# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EmailSummary:
    id: str
    thread_id: str
    subject: str
    sender: str
    to: str
    date: str
    snippet: str
    is_unread: bool
    labels: list[str] = field(default_factory=list)

    def format(self, index: Optional[int] = None) -> str:
        prefix = f"{index}. " if index is not None else ""
        status = "🔴 UNREAD" if self.is_unread else "✅ READ"
        return (
            f"{prefix}📧 {self.subject}\n"
            f"   From    : {self.sender}\n"
            f"   Date    : {self.date}\n"
            f"   ID      : {self.id}\n"
            f"   Status  : {status}\n"
            f"   Preview : {self.snippet}\n"
        )


@dataclass
class EmailContent(EmailSummary):
    body_text: str = ""
    body_html: str = ""
    attachments: list[dict] = field(default_factory=list)


@dataclass
class LabelInfo:
    id: str
    name: str
    label_type: str


# ─────────────────────────────────────────────────────────────────────────────
# Gmail Client
# ─────────────────────────────────────────────────────────────────────────────

class GmailClient:
    """
    Singleton Gmail API client.
    Call initialize() once before using any methods.
    """

    def __init__(self):
        self._service = None

    def initialize(self) -> None:
        """Authenticate and build the Gmail API service."""
        creds: Credentials = get_credentials()
        self._service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service initialized successfully.")

    @property
    def service(self):
        if self._service is None:
            raise RuntimeError(
                "GmailClient not initialized. Call initialize() first."
            )
        return self._service

    # ─────────────────────────────────────────────────────────────────────────
    # List Unread Emails
    # ─────────────────────────────────────────────────────────────────────────

    def list_unread_emails(self, max_results: int = MAX_RESULTS) -> list[EmailSummary]:
        result = (
            self.service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=min(max_results, 100))
            .execute()
        )
        messages = result.get("messages", [])
        summaries = []
        for msg in messages:
            summary = self.get_email_summary(msg["id"])
            if summary:
                summaries.append(summary)
        return summaries

    # ─────────────────────────────────────────────────────────────────────────
    # Get Email Summary (metadata only — fast)
    # ─────────────────────────────────────────────────────────────────────────

    def get_email_summary(self, message_id: str) -> Optional[EmailSummary]:
        try:
            msg = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["Subject", "From", "To", "Date"],
                )
                .execute()
            )
            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }
            label_ids = msg.get("labelIds", [])
            return EmailSummary(
                id=msg["id"],
                thread_id=msg.get("threadId", ""),
                subject=headers.get("subject", "(No Subject)"),
                sender=headers.get("from", ""),
                to=headers.get("to", ""),
                date=headers.get("date", ""),
                snippet=msg.get("snippet", ""),
                is_unread="UNREAD" in label_ids,
                labels=label_ids,
            )
        except Exception as e:
            logger.error(f"Failed to fetch summary for {message_id}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # Get Email Full Content
    # ─────────────────────────────────────────────────────────────────────────

    def get_email_content(self, message_id: str) -> Optional[EmailContent]:
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }
            label_ids = msg.get("labelIds", [])
            payload = msg.get("payload", {})
            plain_text, html_text, attachments = self._extract_body(payload)

            return EmailContent(
                id=msg["id"],
                thread_id=msg.get("threadId", ""),
                subject=headers.get("subject", "(No Subject)"),
                sender=headers.get("from", ""),
                to=headers.get("to", ""),
                date=headers.get("date", ""),
                snippet=msg.get("snippet", ""),
                is_unread="UNREAD" in label_ids,
                labels=label_ids,
                body_text=plain_text,
                body_html=html_text,
                attachments=attachments,
            )
        except Exception as e:
            logger.error(f"Failed to fetch content for {message_id}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # Search Emails
    # ─────────────────────────────────────────────────────────────────────────

    def search_emails(
        self, query: str, max_results: int = MAX_RESULTS
    ) -> list[EmailSummary]:
        result = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=min(max_results, 100))
            .execute()
        )
        messages = result.get("messages", [])
        summaries = []
        for msg in messages:
            summary = self.get_email_summary(msg["id"])
            if summary:
                summaries.append(summary)
        return summaries

    # ─────────────────────────────────────────────────────────────────────────
    # Mark As Read
    # ─────────────────────────────────────────────────────────────────────────

    def mark_as_read(self, message_id: str) -> bool:
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark {message_id} as read: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Trash Email
    # ─────────────────────────────────────────────────────────────────────────

    def trash_email(self, message_id: str) -> bool:
        try:
            self.service.users().messages().trash(
                userId="me",
                id=message_id,
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to trash {message_id}: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # List Labels
    # ─────────────────────────────────────────────────────────────────────────

    def list_labels(self) -> list[LabelInfo]:
        result = self.service.users().labels().list(userId="me").execute()
        labels = result.get("labels", [])
        return [
            LabelInfo(
                id=lbl["id"],
                name=lbl["name"],
                label_type=lbl.get("type", "user"),
            )
            for lbl in labels
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Get Emails By Label
    # ─────────────────────────────────────────────────────────────────────────

    def get_emails_by_label(
        self, label_id: str, max_results: int = MAX_RESULTS
    ) -> list[EmailSummary]:
        result = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                labelIds=[label_id],
                maxResults=min(max_results, 100),
            )
            .execute()
        )
        messages = result.get("messages", [])
        summaries = []
        for msg in messages:
            summary = self.get_email_summary(msg["id"])
            if summary:
                summaries.append(summary)
        return summaries

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_body(
        self, payload: dict, result: Optional[dict] = None
    ) -> tuple[str, str, list[dict]]:
        """Recursively extract plain text, HTML, and attachment info from a MIME tree."""
        if result is None:
            result = {"plain": "", "html": "", "attachments": []}

        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data", "")

        if mime_type == "text/plain" and data:
            result["plain"] += self._decode_base64(data)
        elif mime_type == "text/html" and data:
            result["html"] += self._decode_base64(data)
        elif body.get("attachmentId") and payload.get("filename"):
            result["attachments"].append(
                {
                    "filename": payload["filename"],
                    "mimeType": mime_type,
                    "size": body.get("size", 0),
                    "attachmentId": body["attachmentId"],
                }
            )

        # Recurse into parts
        for part in payload.get("parts", []):
            self._extract_body(part, result)

        return result["plain"], result["html"], result["attachments"]

    @staticmethod
    def _decode_base64(data: str) -> str:
        """Decode a URL-safe base64 encoded string to UTF-8 text."""
        try:
            padded = data + "=" * (4 - len(data) % 4)
            return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
        except Exception:
            return ""

    @staticmethod
    def strip_html(html: str) -> str:
        """Strip HTML tags and decode entities for plain-text display."""
        html = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<[^>]+>", " ", html)
        html = (
            html.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )
        return re.sub(r"\s{2,}", " ", html).strip()


# Singleton shared across all tools
gmail_client = GmailClient()
