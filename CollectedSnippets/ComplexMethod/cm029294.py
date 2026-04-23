async def get_target_id_from_url(self, url: str) -> TargetID:
		"""Get the TargetID from a URL using SessionManager (source of truth)."""
		if not self.session_manager:
			raise RuntimeError('SessionManager not initialized')

		# Search in SessionManager targets (exact match first)
		for target_id, target in self.session_manager.get_all_targets().items():
			if target.target_type in ('page', 'tab') and target.url == url:
				return target_id

		# Still not found, try substring match as fallback
		for target_id, target in self.session_manager.get_all_targets().items():
			if target.target_type in ('page', 'tab') and url in target.url:
				return target_id

		raise ValueError(f'No TargetID found for url={url}')