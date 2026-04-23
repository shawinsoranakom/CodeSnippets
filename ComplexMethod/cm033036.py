def format_comments(
    comment_block: Any,
    *,
    blacklist: Collection[str],
) -> str:
    """Convert Jira comments into a markdown-ish bullet list."""
    if not isinstance(comment_block, dict):
        return ""

    comments = comment_block.get("comments") or []
    lines: list[str] = []
    normalized_blacklist = {email.lower() for email in blacklist if email}

    for comment in comments:
        author = comment.get("author") or {}
        author_email = (author.get("emailAddress") or "").lower()
        if author_email and author_email in normalized_blacklist:
            continue

        author_name = author.get("displayName") or author.get("name") or author_email or "Unknown"
        created = parse_jira_datetime(comment.get("created"))
        created_str = created.isoformat() if created else "Unknown time"
        body = extract_body_text(comment.get("body"))
        if not body:
            continue

        lines.append(f"- {author_name} ({created_str}):\n{body}")

    return "\n\n".join(lines)