async def handle_event(self, event, event_id):
		try:
			logger.info(f'Received event id: {event_id}')
			if not event_id:
				logger.warning('Event ID missing in event data')
				return

			if event_id in self.processed_events:
				logger.info(f'Event {event_id} already processed')
				return
			self.processed_events.add(event_id)

			if 'subtype' in event and event['subtype'] == 'bot_message':
				return

			text = event.get('text')
			user_id = event.get('user')
			if text and text.startswith('$bu '):
				task = text[len('$bu ') :].strip()
				if self.ack:
					try:
						await self.send_message(
							event['channel'], f'<@{user_id}> Starting browser use task...', thread_ts=event.get('ts')
						)
					except Exception as e:
						logger.error(f'Error sending start message: {e}')

				try:
					agent_message = await self.run_agent(task)
					await self.send_message(event['channel'], f'<@{user_id}> {agent_message}', thread_ts=event.get('ts'))
				except Exception as e:
					await self.send_message(event['channel'], f'Error during task execution: {str(e)}', thread_ts=event.get('ts'))
		except Exception as e:
			logger.error(f'Error in handle_event: {str(e)}')