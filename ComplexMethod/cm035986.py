async def get_issue_details(self) -> tuple[str, str]:
        """Fetch issue details from Jira API (cached after first call).

        Returns:
            Tuple of (issue_title, issue_description)

        Raises:
            StartingConvoException: If issue details cannot be fetched
        """
        if self._issue_title is not None and self._issue_description is not None:
            return self._issue_title, self._issue_description

        try:
            url = f'{JIRA_CLOUD_API_URL}/{self.jira_workspace.jira_cloud_id}/rest/api/2/issue/{self.payload.issue_key}'
            async with httpx.AsyncClient(verify=httpx_verify_option()) as client:
                response = await client.get(
                    url,
                    auth=(
                        self.jira_workspace.svc_acc_email,
                        self._decrypted_api_key,
                    ),
                )
                response.raise_for_status()
                issue_payload = response.json()

            if not issue_payload:
                raise StartingConvoException(
                    f'Issue {self.payload.issue_key} not found.'
                )

            self._issue_title = issue_payload.get('fields', {}).get('summary', '')
            self._issue_description = (
                issue_payload.get('fields', {}).get('description', '') or ''
            )

            if not self._issue_title:
                raise StartingConvoException(
                    f'Issue {self.payload.issue_key} does not have a title.'
                )

            logger.info(
                '[Jira] Fetched issue details',
                extra={
                    'issue_key': self.payload.issue_key,
                    'has_description': bool(self._issue_description),
                },
            )

            return self._issue_title, self._issue_description

        except httpx.HTTPStatusError as e:
            logger.error(
                '[Jira] Failed to fetch issue details',
                extra={
                    'issue_key': self.payload.issue_key,
                    'status': e.response.status_code,
                },
            )
            raise StartingConvoException(
                f'Failed to fetch issue details: HTTP {e.response.status_code}'
            )
        except Exception as e:
            if isinstance(e, StartingConvoException):
                raise
            logger.error(
                '[Jira] Failed to fetch issue details',
                extra={'issue_key': self.payload.issue_key, 'error': str(e)},
            )
            raise StartingConvoException(f'Failed to fetch issue details: {str(e)}')