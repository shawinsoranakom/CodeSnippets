def _extract_and_validate(
        self,
        payload: dict,
        user_data: dict,
        event_type: JiraEventType,
        webhook_event: str,
        comment_body: str,
    ) -> JiraPayloadParseResult:
        """Extract common fields and validate required data is present."""
        issue_data = payload.get('issue', {})

        # Extract all fields with empty string defaults (makes them str type)
        issue_id = issue_data.get('id', '')
        issue_key = issue_data.get('key', '')
        user_email = user_data.get('emailAddress', '')
        display_name = user_data.get('displayName', '')
        account_id = user_data.get('accountId', '')
        base_api_url, workspace_name = self._extract_workspace_from_url(
            issue_data.get('self', '')
        )

        # Validate required fields
        missing: list[str] = []
        if not issue_id:
            missing.append('issue.id')
        if not issue_key:
            missing.append('issue.key')
        if not display_name:
            missing.append('user.displayName')
        if not account_id:
            missing.append('user.accountId')
        if not workspace_name:
            missing.append('workspace_name (derived from issue.self)')
        if not base_api_url:
            missing.append('base_api_url (derived from issue.self)')

        if missing:
            return JiraPayloadError(f"Missing required fields: {', '.join(missing)}")

        return JiraPayloadSuccess(
            JiraWebhookPayload(
                event_type=event_type,
                raw_event=webhook_event,
                issue_id=issue_id,
                issue_key=issue_key,
                user_email=user_email,
                display_name=display_name,
                account_id=account_id,
                workspace_name=workspace_name,
                base_api_url=base_api_url,
                comment_body=comment_body,
            )
        )