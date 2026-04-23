def _on_lifecycle_event(self, params: LifecycleEventEvent, session_id: str | None) -> None:
		"""Handle Page.lifecycleEvent for tracking page load timings."""
		try:
			frame_id = params.get('frameId') if hasattr(params, 'get') else getattr(params, 'frameId', None)
			name = params.get('name') if hasattr(params, 'get') else getattr(params, 'name', None)
			timestamp = params.get('timestamp') if hasattr(params, 'get') else getattr(params, 'timestamp', None)

			if not frame_id or not name or frame_id not in self._top_level_pages:
				return

			page_info = self._top_level_pages[frame_id]
			# Use monotonic_start instead of startedDateTime (wall-clock) for timing calculations
			monotonic_start = page_info.get('monotonic_start')

			if name == 'DOMContentLoaded' and monotonic_start is not None:
				# Calculate milliseconds since page start using monotonic timestamps
				try:
					elapsed_ms = int(round((timestamp - monotonic_start) * 1000))
					page_info['onContentLoad'] = max(0, elapsed_ms)
				except Exception:
					pass
			elif name == 'load' and monotonic_start is not None:
				try:
					elapsed_ms = int(round((timestamp - monotonic_start) * 1000))
					page_info['onLoad'] = max(0, elapsed_ms)
				except Exception:
					pass
		except Exception as e:
			self.logger.debug(f'lifecycleEvent handling error: {e}')