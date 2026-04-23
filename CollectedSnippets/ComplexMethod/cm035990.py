def parse_webhook(self, payload: Dict) -> JobContext | None:
        event_type = payload.get('webhookEvent')

        if event_type == 'comment_created':
            comment_data = payload.get('comment', {})
            comment = comment_data.get('body', '')

            if '@openhands' not in comment:
                return None

            issue_data = payload.get('issue', {})
            issue_id = issue_data.get('id')
            issue_key = issue_data.get('key')
            base_api_url = issue_data.get('self', '').split('/rest/')[0]

            user_data = comment_data.get('author', {})
            user_email = user_data.get('emailAddress')
            display_name = user_data.get('displayName')
            user_key = user_data.get('key')
        elif event_type == 'jira:issue_updated':
            changelog = payload.get('changelog', {})
            items = changelog.get('items', [])
            labels = [
                item.get('toString', '')
                for item in items
                if item.get('field') == 'labels' and 'toString' in item
            ]

            if 'openhands' not in labels:
                return None

            issue_data = payload.get('issue', {})
            issue_id = issue_data.get('id')
            issue_key = issue_data.get('key')
            base_api_url = issue_data.get('self', '').split('/rest/')[0]

            user_data = payload.get('user', {})
            user_email = user_data.get('emailAddress')
            display_name = user_data.get('displayName')
            user_key = user_data.get('key')
            comment = ''
        else:
            return None

        workspace_name = ''

        parsedUrl = urlparse(base_api_url)
        if parsedUrl.hostname:
            workspace_name = parsedUrl.hostname

        if not all(
            [
                issue_id,
                issue_key,
                user_email,
                display_name,
                user_key,
                workspace_name,
                base_api_url,
            ]
        ):
            return None

        return JobContext(
            issue_id=issue_id,
            issue_key=issue_key,
            user_msg=comment,
            user_email=user_email,
            display_name=display_name,
            platform_user_id=user_key,
            workspace_name=workspace_name,
            base_api_url=base_api_url,
        )