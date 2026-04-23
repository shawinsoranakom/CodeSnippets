async def receive_message(self, message: Message):
        """Process incoming Jira webhook message.

        Flow:
        1. Parse webhook payload
        2. Validate workspace exists and is active
        3. Authenticate user
        4. Create view (includes fetching issue details and selecting repository)
        5. Start job

        Each step has clear logging for traceability.
        """
        raw_payload = message.message.get('payload', {})

        # Step 1: Parse webhook payload
        logger.info(
            '[Jira] Received webhook',
            extra={'raw_payload': raw_payload},
        )

        parse_result = self.payload_parser.parse(raw_payload)

        if isinstance(parse_result, JiraPayloadSkipped):
            logger.info(
                '[Jira] Webhook skipped', extra={'reason': parse_result.skip_reason}
            )
            return

        if isinstance(parse_result, JiraPayloadError):
            logger.warning(
                '[Jira] Webhook parse failed', extra={'error': parse_result.error}
            )
            return

        payload = parse_result.payload
        logger.info(
            '[Jira] Processing webhook',
            extra={
                'event_type': payload.event_type.value,
                'issue_key': payload.issue_key,
                'user_email': payload.user_email,
            },
        )

        # Step 2: Validate workspace
        workspace = await self._get_active_workspace(payload)
        if not workspace:
            return

        # Step 3: Authenticate user
        jira_user, saas_user_auth = await self._authenticate_user(payload, workspace)
        if not jira_user or not saas_user_auth:
            return

        # Step 4: Create view (includes issue details fetch and repo selection)
        decrypted_api_key = self.token_manager.decrypt_text(workspace.svc_acc_api_key)

        try:
            view = await JiraFactory.create_view(
                payload=payload,
                workspace=workspace,
                user=jira_user,
                user_auth=saas_user_auth,
                decrypted_api_key=decrypted_api_key,
            )
        except RepositoryNotFoundError as e:
            logger.warning(
                '[Jira] Repository not found',
                extra={'issue_key': payload.issue_key, 'error': str(e)},
            )
            await self._send_error_from_payload(payload, workspace, str(e))
            return
        except StartingConvoException as e:
            logger.warning(
                '[Jira] View creation failed',
                extra={'issue_key': payload.issue_key, 'error': str(e)},
            )
            await self._send_error_from_payload(payload, workspace, str(e))
            return
        except Exception as e:
            logger.error(
                '[Jira] Unexpected error creating view',
                extra={'issue_key': payload.issue_key, 'error': str(e)},
                exc_info=True,
            )
            await self._send_error_from_payload(
                payload,
                workspace,
                'Failed to initialize conversation. Please try again.',
            )
            return

        # Step 5: Start job
        await self.start_job(view)