async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        """Process events for GitHub V1 integration."""
        # Only handle ConversationStateUpdateEvent for execution_status
        if not isinstance(event, ConversationStateUpdateEvent):
            return None

        if event.key != 'execution_status':
            return None

        # Log ALL terminal states for monitoring (finished, error, stuck)
        _logger.info('[GitHub V1] Callback agent state was %s', event)

        # Only request summary when execution has finished successfully
        if event.value != 'finished':
            return None

        _logger.info(
            '[GitHub V1] Should request summary: %s', self.should_request_summary
        )

        if not self.should_request_summary:
            return None

        self.should_request_summary = False

        try:
            _logger.info(f'[GitHub V1] Requesting summary {conversation_id}')
            summary = await self._request_summary(conversation_id)
            _logger.info(
                f'[GitHub V1] Posting summary {conversation_id}',
                extra={'summary': summary},
            )
            await self._post_summary_to_github(summary)

            return EventCallbackResult(
                status=EventCallbackResultStatus.SUCCESS,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
                detail=summary,
            )
        except Exception as e:
            # Check if we have installation ID and credentials before posting
            can_post_error = bool(
                self.github_view_data.get('installation_id')
                and GITHUB_APP_CLIENT_ID
                and GITHUB_APP_PRIVATE_KEY
            )
            await handle_callback_error(
                error=e,
                conversation_id=conversation_id,
                service_name='GitHub',
                service_logger=_logger,
                can_post_error=can_post_error,
                post_error_func=self._post_summary_to_github,
            )

            return EventCallbackResult(
                status=EventCallbackResultStatus.ERROR,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
                detail=str(e),
            )