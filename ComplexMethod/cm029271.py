def attach_to_session(self) -> None:
		"""Attach watchdog to its browser session and start monitoring.

		This method handles event listener registration. The watchdog is already
		bound to a browser session via self.browser_session from initialization.
		"""
		# Register event handlers automatically based on method names
		assert self.browser_session is not None, 'Root CDP client not initialized - browser may not be connected yet'

		from browser_use.browser import events

		event_classes = {}
		for name in dir(events):
			obj = getattr(events, name)
			if inspect.isclass(obj) and issubclass(obj, BaseEvent) and obj is not BaseEvent:
				event_classes[name] = obj

		# Find all handler methods (on_EventName)
		registered_events = set()
		for method_name in dir(self):
			if method_name.startswith('on_') and callable(getattr(self, method_name)):
				# Extract event name from method name (on_EventName -> EventName)
				event_name = method_name[3:]  # Remove 'on_' prefix

				if event_name in event_classes:
					event_class = event_classes[event_name]

					# ASSERTION: If LISTENS_TO is defined, enforce it
					if self.LISTENS_TO:
						assert event_class in self.LISTENS_TO, (
							f'[{self.__class__.__name__}] Handler {method_name} listens to {event_name} '
							f'but {event_name} is not declared in LISTENS_TO: {[e.__name__ for e in self.LISTENS_TO]}'
						)

					handler = getattr(self, method_name)

					# Use the static helper to attach the handler
					self.attach_handler_to_session(self.browser_session, event_class, handler)
					registered_events.add(event_class)

		# ASSERTION: If LISTENS_TO is defined, ensure all declared events have handlers
		if self.LISTENS_TO:
			missing_handlers = set(self.LISTENS_TO) - registered_events
			if missing_handlers:
				missing_names = [e.__name__ for e in missing_handlers]
				self.logger.warning(
					f'[{self.__class__.__name__}] LISTENS_TO declares {missing_names} '
					f'but no handlers found (missing on_{"_, on_".join(missing_names)} methods)'
				)