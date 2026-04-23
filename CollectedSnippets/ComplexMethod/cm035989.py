async def validate_request(
        self, request: Request
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Verify Jira DC webhook signature."""
        signature_header = request.headers.get('x-hub-signature')
        signature = signature_header.split('=')[1] if signature_header else None
        body = await request.body()
        payload = await request.json()
        workspace_name = ''

        if payload.get('webhookEvent') == 'comment_created':
            selfUrl = payload.get('comment', {}).get('author', {}).get('self')
        elif payload.get('webhookEvent') == 'jira:issue_updated':
            selfUrl = payload.get('user', {}).get('self')
        else:
            workspace_name = ''

        parsedUrl = urlparse(selfUrl)
        if parsedUrl.hostname:
            workspace_name = parsedUrl.hostname

        if not workspace_name:
            logger.warning('[Jira DC] No workspace name found in webhook payload')
            return False, None, None

        if not signature:
            logger.warning('[Jira DC] No signature found in webhook headers')
            return False, None, None

        workspace = await self.integration_store.get_workspace_by_name(workspace_name)

        if not workspace:
            logger.warning('[Jira DC] Could not identify workspace for webhook')
            return False, None, None

        if workspace.status != 'active':
            logger.warning(f'[Jira DC] Workspace {workspace.id} is not active')
            return False, None, None

        webhook_secret = self.token_manager.decrypt_text(workspace.webhook_secret)
        digest = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()

        if hmac.compare_digest(signature, digest):
            logger.info('[Jira DC] Webhook signature verified successfully')
            return True, signature, payload

        return False, None, None