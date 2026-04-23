def setup_event_bus_listener(self) -> None:
		"""Setup listener for browser session event bus."""
		if not self.browser_session or not self.browser_session.event_bus:
			return

		# Clean up any existing handler before registering a new one
		if self._event_bus_handler_func is not None:
			try:
				# Remove handler from the event bus's internal handlers dict
				if hasattr(self.browser_session.event_bus, 'handlers'):
					# Find and remove our handler function from all event patterns
					for event_type, handler_list in list(self.browser_session.event_bus.handlers.items()):
						# Remove our specific handler function object
						if self._event_bus_handler_func in handler_list:
							handler_list.remove(self._event_bus_handler_func)
							logging.debug(f'Removed old handler from event type: {event_type}')
			except Exception as e:
				logging.debug(f'Error cleaning up event bus handler: {e}')
			self._event_bus_handler_func = None
			self._event_bus_handler_id = None

		try:
			# Get the events log widget
			events_log = self.query_one('#events-log', RichLog)
		except Exception:
			# Widget not ready yet
			return

		# Create handler to log all events
		def log_event(event):
			event_name = event.__class__.__name__
			# Format event data nicely
			try:
				if hasattr(event, 'model_dump'):
					event_data = event.model_dump(exclude_unset=True)
					# Remove large fields
					if 'screenshot' in event_data:
						event_data['screenshot'] = '<bytes>'
					if 'dom_state' in event_data:
						event_data['dom_state'] = '<truncated>'
					event_str = str(event_data) if event_data else ''
				else:
					event_str = str(event)

				# Truncate long strings
				if len(event_str) > 200:
					event_str = event_str[:200] + '...'

				events_log.write(f'[yellow]→ {event_name}[/] {event_str}')
			except Exception as e:
				events_log.write(f'[red]→ {event_name}[/] (error formatting: {e})')

		# Store the handler function before registering it
		self._event_bus_handler_func = log_event
		self._event_bus_handler_id = id(log_event)

		# Register wildcard handler for all events
		self.browser_session.event_bus.on('*', log_event)
		logging.debug(f'Registered new event bus handler with id: {self._event_bus_handler_id}')