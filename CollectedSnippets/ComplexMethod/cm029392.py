async def handle_event(self, event: BaseEvent) -> None:
		"""Handle an event by sending it to the cloud"""
		try:
			# If cloud sync is disabled, don't handle any events
			if not self.enabled:
				return

			# Extract session ID from CreateAgentSessionEvent
			if event.event_type == 'CreateAgentSessionEvent' and hasattr(event, 'id'):
				self.session_id = str(event.id)  # type: ignore

			# Send events based on authentication status and context
			if self.auth_client.is_authenticated:
				# User is authenticated - send all events
				await self._send_event(event)
			elif self.allow_session_events_for_auth:
				# Special case: allow ALL events during auth flow
				await self._send_event(event)
				# Mark auth flow as active when we see a session event
				if event.event_type == 'CreateAgentSessionEvent':
					self.auth_flow_active = True
			else:
				# User is not authenticated and no auth in progress - don't send anything
				logger.debug(f'Skipping event {event.event_type} - user not authenticated')

		except Exception as e:
			logger.error(f'Failed to handle {event.event_type} event: {type(e).__name__}: {e}', exc_info=True)