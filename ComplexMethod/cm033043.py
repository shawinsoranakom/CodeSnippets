def _issue_to_document(self, issue: Issue) -> Document | None:
        fields = issue.raw.get("fields", {})
        summary = fields.get("summary") or ""
        description_text = extract_body_text(fields.get("description"))
        comments_text = (
            format_comments(
                fields.get("comment"),
                blacklist=self.comment_email_blacklist,
            )
            if self.include_comments
            else ""
        )
        attachments_text = format_attachments(fields.get("attachment"))

        reporter_name, reporter_email = extract_user(fields.get("reporter"))
        assignee_name, assignee_email = extract_user(fields.get("assignee"))
        status = extract_named_value(fields.get("status"))
        priority = extract_named_value(fields.get("priority"))
        issue_type = extract_named_value(fields.get("issuetype"))
        project = fields.get("project") or {}

        issue_url = build_issue_url(self.jira_base_url, issue.key)

        metadata_lines = [
            f"key: {issue.key}",
            f"url: {issue_url}",
            f"summary: {summary}",
            f"status: {status or 'Unknown'}",
            f"priority: {priority or 'Unspecified'}",
            f"issue_type: {issue_type or 'Unknown'}",
            f"project: {project.get('name') or ''}",
            f"project_key: {project.get('key') or self.project_key or ''}",
        ]

        if reporter_name:
            metadata_lines.append(f"reporter: {reporter_name}")
        if reporter_email:
            metadata_lines.append(f"reporter_email: {reporter_email}")
        if assignee_name:
            metadata_lines.append(f"assignee: {assignee_name}")
        if assignee_email:
            metadata_lines.append(f"assignee_email: {assignee_email}")
        if fields.get("labels"):
            metadata_lines.append(f"labels: {', '.join(fields.get('labels'))}")

        created_dt = parse_jira_datetime(fields.get("created"))
        updated_dt = parse_jira_datetime(fields.get("updated")) or created_dt or datetime.now(timezone.utc)
        metadata_lines.append(f"created: {created_dt.isoformat() if created_dt else ''}")
        metadata_lines.append(f"updated: {updated_dt.isoformat() if updated_dt else ''}")

        sections: list[str] = [
            "---",
            "\n".join(filter(None, metadata_lines)),
            "---",
            "",
            "## Description",
            description_text or "No description provided.",
        ]

        if comments_text:
            sections.extend(["", "## Comments", comments_text])
        if attachments_text:
            sections.extend(["", "## Attachments", attachments_text])

        blob_text = "\n".join(sections).strip() + "\n"
        blob = blob_text.encode("utf-8")

        if len(blob) > self.max_ticket_size:
            logger.info(f"[Jira] Skipping {issue.key} because it exceeds the maximum size of {self.max_ticket_size} bytes.")
            return None

        semantic_identifier = f"{issue.key}: {summary}" if summary else issue.key

        return Document(
            id=issue_url,
            source=DocumentSource.JIRA,
            semantic_identifier=semantic_identifier,
            extension=".md",
            blob=blob,
            doc_updated_at=updated_dt,
            size_bytes=len(blob),
        )