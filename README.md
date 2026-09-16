# 📬 Gmail MCP Server (Python)

A **Model Context Protocol (MCP)** server written in **Python** that connects to your Gmail inbox and exposes powerful email tools to any MCP-compatible AI client (Claude Desktop, Cursor, Antigravity IDE, etc.).

Ask your AI assistant things like:
- *"Show me all my unread emails"*
- *"What did my boss send me this week?"*
- *"Read the full content of the email about the invoice"*
- *"Mark all unread newsletters as read"*
- *"Search for emails with attachments from last month"*

---

## ✨ Features

| Tool | Description |
|------|-------------|
| `list_unread_emails` | List all unread emails with subject, sender, date, and preview |
| `get_email_content` | Read the full body of any email by its ID |
| `get_email_summary` | Get metadata (subject, from, date) for any email |
| `search_emails` | Search using Gmail's full query syntax |
| `mark_as_read` | Mark one or multiple emails as read |
| `trash_emails` | Move one or multiple emails to the Trash |
| `list_labels` | List all Gmail labels (system + custom) |
| `get_emails_by_label` | Fetch emails from a specific label (INBOX, SPAM, etc.) |

---

## 🏗️ Architecture

```
AI Client (Claude Desktop / Cursor / AGY)
        │
        │  MCP protocol over stdio
        ▼
┌─────────────────────────────────────────┐
│         Gmail MCP Server (Python)        │
 │  ┌──────────────────────────────────┐   │
 │  │  MCP Server (mcp Python SDK)     │   │
 │  │  server.py — 8 tools registered  │   │
 │  └──────────────┬───────────────────┘   │
 │  ┌──────────────▼───────────────────┐   │
 │  │  GmailClient (gmail_client.py)   │   │
 │  │  google-api-python-client        │   │
 │  └──────────────┬───────────────────┘   │
 │  ┌──────────────▼───────────────────┐   │
 │  │  OAuth2 Auth (auth.py)           │   │
 │  │  google-auth-oauthlib            │   │
 │  │  token.json cached               │   │
 │  └──────────────┬───────────────────┘   │
 └─────────────────┼───────────────────────┘
                   │
         Google Gmail REST API
```

## 🔌 Ways to Connect

This MCP server can be used in two primary ways:
1. **Interactive Client (`client.py`)**: A direct command-line interface provided in this repository.
2. **AI Clients**: Integrate it as a tool server with AI apps like Claude, Cursor, or Antigravity IDE.

---

## 📁 Project Structure

```
mcp-gmail/
├── src/
│   ├── __init__.py
│   ├── server.py           # MCP server entry point — registers all 8 tools
│   ├── auth.py             # OAuth2 authentication (first-time + token refresh)
│   ├── gmail_client.py     # Gmail API wrapper with typed dataclasses
│   └── tools/
│       ├── __init__.py
│       ├── list_unread.py  # list_unread_emails
│       ├── get_content.py  # get_email_content + get_email_summary
│       ├── search_emails.py # search_emails
│       ├── mark_read.py    # mark_as_read
│       ├── trash_email.py  # trash_emails
│       └── list_labels.py  # list_labels + get_emails_by_label
├── credentials/
│   └── .gitkeep            # ← Place credentials.json here (git-ignored)
├── venv/                   # Python virtual environment
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites

- **Python 3.10+** (3.13 recommended)
- A **Google Account** with Gmail
- Access to **Google Cloud Console**

---

### Step 1 — Clone & Create Virtual Environment

```bash
cd /path/to/mcp-gmail

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Step 2 — Create Google Cloud Credentials

You need OAuth2 credentials from Google Cloud Console.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. **Create a new project**:
   - Click the project selector → **New Project** → name it `mcp-gmail` → **Create**

3. **Enable the Gmail API**:
   - Go to **APIs & Services → Library**
   - Search **"Gmail API"** → Click it → **Enable**

4. **Configure OAuth Consent Screen**:
   - Go to **APIs & Services → OAuth consent screen**
   - Select **External** → **Create**
   - Fill in:
     - App name: `Gmail MCP Server`
     - User support email: your Gmail address
     - Developer contact email: your Gmail address
   - **Save and Continue** through all screens
   - On **Test Users** page: **+ Add Users** → add your Gmail → **Save and Continue**

5. **Create OAuth2 Credentials**:
   - Go to **APIs & Services → Credentials**
   - Click **+ Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: `Gmail MCP Client`
   - Click **Create** → **Download JSON**

6. **Place the downloaded file** in the credentials folder:
   ```bash
   mv ~/Downloads/client_secret_*.json credentials/credentials.json
   ```

---

### Step 3 — Configure Environment

```bash
cp .env.example .env
```

The defaults in `.env` work fine. Only edit if you changed file paths:

```env
CREDENTIALS_PATH=./credentials/credentials.json
TOKEN_PATH=./credentials/token.json
MAX_RESULTS=20
```

---

### Step 4 — Authorize Gmail Access (First-Time Only)

```bash
source venv/bin/activate
python -m src.auth
```

This will:
1. Open your browser to the Google OAuth consent page
2. Ask you to sign in and grant access
3. Automatically capture the token and save `credentials/token.json`

> ⚠️ **If you see "This app isn't verified"** — click **Advanced → Go to Gmail MCP Server (unsafe)**. This is expected for apps in test/development mode.

After this step, `token.json` is saved and will be auto-refreshed forever — you never need to re-authorize.

---

### Step 5 — Test the Server

```bash
source venv/bin/activate
python -m src.server
```

You should see:
```
✅ Gmail authentication successful
🚀 Gmail MCP Server running (stdio transport)
   Tools: list_unread_emails, get_email_content, ...
```
```

Press `Ctrl+C` to stop. 

## 🧪 Testing and Usage Guide

Because this codebase relies on the low-level `mcp` Python SDK, the standard `mcp dev` tool cannot be used to visually inspect the server. Instead, use the methods below.

---

### 1. Local Python Testing (No AI required)

We have provided a robust interactive CLI tool that allows you to directly call the MCP server functions without needing an LLM.

**Steps:**
1. Ensure your virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```
2. Run the client script:
   ```bash
   python client.py
   ```
3. An interactive menu will appear in your terminal. You can select tools like `search_emails` or `list_unread_emails` and provide input parameters. The output will be formatted and printed directly to your console.

---

### 2. Testing in Claude Desktop

You can attach this server to Claude Desktop to give Claude direct access to your Gmail.

**Steps:**
1. Open the Claude Desktop configuration file:
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
2. Add the following configuration (replace the paths with your absolute paths):
   ```json
   {
     "mcpServers": {
       "gmail": {
         "command": "/absolute/path/to/mcp-gmail/venv/bin/python",
         "args": ["-m", "src.server"],
         "cwd": "/absolute/path/to/mcp-gmail",
         "env": {
           "CREDENTIALS_PATH": "/absolute/path/to/mcp-gmail/credentials/credentials.json",
           "TOKEN_PATH": "/absolute/path/to/mcp-gmail/credentials/token.json"
         }
       }
     }
   }
   ```
3. Completely quit and restart Claude Desktop.
4. You should now see a small "hammer" icon inside Claude indicating the Gmail tools are available. Test it by asking: *"Can you check my unread emails?"*

---

### 3. Testing AI Skills (Antigravity IDE)

This repository includes a custom `.agents/` folder that contains a `gmail-daily-overview` AI Skill. 

**What are Skills?**
Skills are repeatable, prompt-engineered workflows that the AI can execute perfectly every time. 

**Steps:**
1. Open this repository folder in the **Antigravity IDE**.
2. The IDE will automatically discover the `.agents/skills` folder.
3. In the IDE chat, simply type:
   ```
   @gmail-daily-overview
   ```
4. The AI agent will run the skill. It will:
   - Search your inbox for emails received in the last 48 hours.
   - Automatically delete known promotional/spam emails using the `trash_emails` tool.
   - Present a clean markdown overview of your important emails.

> [!NOTE]
> The `.agents/mcp_config.json` file inside the `.agents` folder is used by the IDE to connect to the MCP server. Since this config file uses absolute paths specific to your local machine, it is intentionally excluded from Git.

---

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `python -m src.auth` | Run first-time OAuth2 authorization |
| `python -m src.server` | Start the MCP server |

---

## 🔍 Tool Reference

### `list_unread_emails`

Lists all unread emails in your inbox.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_results` | number | No | 20 | Max emails to return (max: 100) |

**Example prompt:** *"Show me my unread emails"*

---

### `get_email_content`

Fetches the full body of a specific email.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | Yes | The Gmail message ID |

**Example prompt:** *"Read the full content of that email"*

---

### `get_email_summary`

Gets lightweight metadata for an email (no body fetch — faster).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | Yes | The Gmail message ID |

---

### `search_emails`

Search emails using Gmail's query syntax.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Gmail search query |
| `max_results` | number | No | 20 | Max results (max: 100) |

**Query Examples:**
```
from:boss@company.com              # From a specific sender
subject:invoice                    # Subject contains "invoice"
is:unread                          # Only unread emails
has:attachment                     # Emails with attachments
after:2024/01/01                   # After Jan 1, 2024
before:2024/12/31                  # Before Dec 31, 2024
from:github.com is:unread          # Unread from GitHub
label:work                         # Emails with "work" label
in:spam                            # Emails in spam folder
```

---

### `mark_as_read`

Marks one or more emails as read.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_ids` | string | Yes | Single ID or comma-separated list |

---

### `trash_emails`

Moves one or more emails to the Trash.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_ids` | string | Yes | Single ID or comma-separated list |

---

### `list_labels`

Lists all Gmail labels. No parameters needed.

---

### `get_emails_by_label`

Fetches emails from a specific label.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `label_id` | string | Yes | — | Label ID (e.g., `INBOX`, `SENT`, `SPAM`) |
| `max_results` | number | No | 20 | Max emails to return |

**Common System Label IDs:**
| Label ID | Description |
|----------|-------------|
| `INBOX` | Inbox |
| `SENT` | Sent mail |
| `SPAM` | Spam folder |
| `TRASH` | Trash |
| `STARRED` | Starred |
| `IMPORTANT` | Priority inbox |
| `UNREAD` | All unread |
| `DRAFT` | Drafts |

---

## 🔐 Security Notes

- **Never commit** `credentials.json` or `token.json` — both are in `.gitignore`
- Token is stored in `credentials/token.json` and auto-refreshed
- OAuth scopes used:
  - `gmail.readonly` — for reading emails and labels
  - `gmail.modify` — for marking emails as read and moving to Trash (bypassing trash to permanently delete is not permitted by this scope)

---

## 🐛 Troubleshooting

**`FileNotFoundError: credentials.json not found`**
→ Place `credentials.json` in the `credentials/` folder (Step 2 above).

**`Token expired / invalid_grant`**
→ Delete `credentials/token.json` and run `python -m src.auth` again.

**`Error: redirect_uri_mismatch`**
→ In Google Cloud Console → Credentials → your OAuth client → Authorized redirect URIs → add `http://localhost`.

**`This app isn't verified` warning**
→ Click **Advanced → Go to Gmail MCP Server (unsafe)**. Normal for test-mode apps.

**Server doesn't appear in Claude Desktop**
→ Use the **absolute path** to `venv/bin/python`. Run `which python` inside the activated venv to confirm.
→ Restart Claude Desktop after editing the config.

**`ModuleNotFoundError`**
→ Make sure you activated the venv (`source venv/bin/activate`) before running.

---

## 📄 License

MIT
