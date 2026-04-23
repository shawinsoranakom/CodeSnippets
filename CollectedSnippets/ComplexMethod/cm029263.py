def copy_old_config_names_to_new(self) -> Self:
		"""Copy old config window_width & window_height to window_size."""
		if self.window_width or self.window_height:
			logger.warning(
				f'⚠️ BrowserProfile(window_width=..., window_height=...) are deprecated, use BrowserProfile(window_size={"width": 1920, "height": 1080}) instead.'
			)
			window_size = self.window_size or ViewportSize(width=0, height=0)
			window_size['width'] = window_size['width'] or self.window_width or 1920
			window_size['height'] = window_size['height'] or self.window_height or 1080
			self.window_size = window_size

		return self