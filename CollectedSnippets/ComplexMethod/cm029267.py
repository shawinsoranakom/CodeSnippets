def detect_display_configuration(self) -> None:
		"""
		Detect the system display size and initialize the display-related config defaults:
		        screen, window_size, window_position, viewport, no_viewport, device_scale_factor
		"""

		display_size = get_display_size()
		has_screen_available = bool(display_size)
		self.screen = self.screen or display_size or ViewportSize(width=1920, height=1080)

		# if no headless preference specified, prefer headful if there is a display available
		if self.headless is None:
			self.headless = not has_screen_available

		# Determine viewport behavior based on mode and user preferences
		user_provided_viewport = self.viewport is not None

		if self.headless:
			# Headless mode: always use viewport for content size control
			self.viewport = self.viewport or self.window_size or self.screen
			self.window_position = None
			self.window_size = None
			self.no_viewport = False
		else:
			# Headful mode: respect user's viewport preference
			self.window_size = self.window_size or self.screen

			if user_provided_viewport:
				# User explicitly set viewport - enable viewport mode
				self.no_viewport = False
			else:
				# Default headful: content fits to window (no viewport)
				self.no_viewport = True if self.no_viewport is None else self.no_viewport

		# Handle special requirements (device_scale_factor forces viewport mode)
		if self.device_scale_factor and self.no_viewport is None:
			self.no_viewport = False

		# Finalize configuration
		if self.no_viewport:
			# No viewport mode: content adapts to window
			self.viewport = None
			self.device_scale_factor = None
			self.screen = None
			assert self.viewport is None
			assert self.no_viewport is True
		else:
			# Viewport mode: ensure viewport is set
			self.viewport = self.viewport or self.screen
			self.device_scale_factor = self.device_scale_factor or 1.0
			assert self.viewport is not None
			assert self.no_viewport is False

		assert not (self.headless and self.no_viewport), 'headless=True and no_viewport=True cannot both be set at the same time'