---
name: gmail-daily-overview
description: Uses the Gmail MCP to search for emails from today and yesterday, and provides a structured overview.
---

# Gmail Daily Overview Skill

When the user asks you to run this skill or generate a daily overview of their emails, follow these steps strictly:

1. **Calculate Dates**: Determine today's date and yesterday's date based on the current local time in your environment.
2. **Search Emails**: Use the Gmail MCP tool (`search_emails`) to find recent emails. 
   - Construct a Gmail query using the `after:` operator. For example: `after:YYYY/MM/DD` (using yesterday's date) to catch all emails from yesterday and today.
3. **Analyze Results**: Read the summaries and metadata of the emails returned by the search. If certain emails seem highly important, you may optionally use `get_email_content` to read their full body.
4. **Clean Up Inbox**: Identify clearly unwanted emails (e.g., pure spam, obvious and unimportant promotions, or generic system alerts that do not require tracking). Use the `trash_emails` tool to delete them. (Be conservative: do not delete anything that might be important).
5. **Generate Report**: Present a well-formatted Markdown summary to the user.
   - **Action Required**: Highlight any urgent emails from real people or important services.
   - **Updates**: Summarize work threads, notifications, or general updates.
   - **Newsletters & Automated**: Group less important automated emails at the bottom.
   - **Deleted Emails**: List the emails that you automatically moved to the Trash, so the user knows what was deleted.
6. **Format**: Use lists and bold text for readability. Do not output raw JSON.
