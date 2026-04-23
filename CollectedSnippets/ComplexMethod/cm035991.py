async def receive_message(self, message: Message):
        """Process incoming Jira DC webhook message."""

        payload = message.message.get('payload', {})
        job_context = self.parse_webhook(payload)

        if not job_context:
            logger.info('[Jira DC] Webhook does not match trigger conditions')
            return

        workspace = await self.integration_store.get_workspace_by_name(
            job_context.workspace_name
        )
        if not workspace:
            logger.warning(
                f'[Jira DC] No workspace found for email domain: {job_context.user_email}'
            )
            await self._send_error_comment(
                job_context,
                'Your workspace is not configured with Jira DC integration.',
                None,
            )
            return

        # Prevent any recursive triggers from the service account
        if job_context.user_email == workspace.svc_acc_email:
            return

        if workspace.status != 'active':
            logger.warning(f'[Jira DC] Workspace {workspace.id} is not active')
            await self._send_error_comment(
                job_context,
                'Jira DC integration is not active for your workspace.',
                workspace,
            )
            return

        # Authenticate user
        jira_dc_user, saas_user_auth = await self.authenticate_user(
            job_context.user_email, job_context.platform_user_id, workspace.id
        )
        if not jira_dc_user or not saas_user_auth:
            logger.warning(
                f'[Jira DC] User authentication failed for {job_context.user_email}'
            )
            await self._send_error_comment(
                job_context,
                f'User {job_context.user_email} is not authenticated or active in the Jira DC integration.',
                workspace,
            )
            return

        # Get issue details
        try:
            api_key = self.token_manager.decrypt_text(workspace.svc_acc_api_key)
            issue_title, issue_description = await self.get_issue_details(
                job_context, api_key
            )
            job_context.issue_title = issue_title
            job_context.issue_description = issue_description
        except Exception as e:
            logger.error(f'[Jira DC] Failed to get issue context: {str(e)}')
            await self._send_error_comment(
                job_context,
                'Failed to retrieve issue details. Please check the issue key and try again.',
                workspace,
            )
            return

        try:
            # Create Jira DC view
            jira_dc_view = await JiraDcFactory.create_jira_dc_view_from_payload(
                job_context,
                saas_user_auth,
                jira_dc_user,
                workspace,
            )
        except Exception as e:
            logger.error(
                f'[Jira DC] Failed to create jira dc view: {str(e)}', exc_info=True
            )
            await self._send_error_comment(
                job_context,
                'Failed to initialize conversation. Please try again.',
                workspace,
            )
            return

        if not await self.is_job_requested(message, jira_dc_view):
            return

        await self.start_job(jira_dc_view)