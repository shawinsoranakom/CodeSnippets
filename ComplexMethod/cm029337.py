def _on_frame_navigated(self, params: FrameNavigatedEvent, session_id: str | None) -> None:
		"""Handle Page.frameNavigated to update page title from DOM."""
		try:
			frame = params.get('frame') if hasattr(params, 'get') else getattr(params, 'frame', None)
			if not frame:
				return

			frame_id = frame.get('id') if isinstance(frame, dict) else getattr(frame, 'id', None)
			title = (
				frame.get('name') or frame.get('url')
				if isinstance(frame, dict)
				else getattr(frame, 'name', None) or getattr(frame, 'url', None)
			)

			if frame_id and frame_id in self._top_level_pages:
				# Try to get actual page title via Runtime.evaluate if possible
				# For now, use frame name or URL as fallback
				if title:
					self._top_level_pages[frame_id]['title'] = str(title)
		except Exception as e:
			self.logger.debug(f'frameNavigated handling error: {e}')