async def _send_event(self, event: BaseEvent) -> None:
		"""Send event to cloud API"""
		try:
			headers = {}

			# Override user_id only if it's not already set to a specific value
			# This allows CLI and other code to explicitly set temp user_id when needed
			if self.auth_client and self.auth_client.is_authenticated:
				# Only override if we're fully authenticated and event doesn't have temp user_id
				current_user_id = getattr(event, 'user_id', None)
				if current_user_id != TEMP_USER_ID:
					setattr(event, 'user_id', str(self.auth_client.user_id))
			else:
				# Set temp user_id if not already set
				if not hasattr(event, 'user_id') or not getattr(event, 'user_id', None):
					setattr(event, 'user_id', TEMP_USER_ID)

			# Add auth headers if available
			if self.auth_client:
				headers.update(self.auth_client.get_headers())

			# Send event (batch format with direct BaseEvent serialization)
			async with httpx.AsyncClient() as client:
				# Serialize event and add device_id to all events
				event_data = event.model_dump(mode='json')
				if self.auth_client and self.auth_client.device_id:
					event_data['device_id'] = self.auth_client.device_id

				response = await client.post(
					f'{self.base_url.rstrip("/")}/api/v1/events',
					json={'events': [event_data]},
					headers=headers,
					timeout=10.0,
				)

				if response.status_code >= 400:
					# Log error but don't raise - we want to fail silently
					logger.debug(
						f'Failed to send sync event: POST {response.request.url} {response.status_code} - {response.text}'
					)
		except httpx.TimeoutException:
			logger.debug(f'Event send timed out after 10 seconds: {event}')
		except httpx.ConnectError as e:
			# logger.warning(f'⚠️ Failed to connect to cloud service at {self.base_url}: {e}')
			pass
		except httpx.HTTPError as e:
			logger.debug(f'HTTP error sending event {event}: {type(e).__name__}: {e}')
		except Exception as e:
			logger.debug(f'Unexpected error sending event {event}: {type(e).__name__}: {e}')