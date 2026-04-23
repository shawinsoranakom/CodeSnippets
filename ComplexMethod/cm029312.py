async def _save_storage_state(self, path: str | None = None) -> None:
		"""Save browser storage state to file."""
		async with self._save_lock:
			# Check if CDP client is available
			assert await self.browser_session.get_or_create_cdp_session(target_id=None)

			save_path = path or self.browser_session.browser_profile.storage_state
			if not save_path:
				return

			# Skip saving if the storage state is already a dict (indicates it was loaded from memory)
			# We only save to file if it started as a file path
			if isinstance(save_path, dict):
				self.logger.debug('[StorageStateWatchdog] Storage state is already a dict, skipping file save')
				return

			try:
				# Get current storage state using CDP
				storage_state = await self.browser_session._cdp_get_storage_state()

				# Update our last known state
				self._last_cookie_state = storage_state.get('cookies', []).copy()

				# Convert path to Path object
				json_path = Path(save_path).expanduser().resolve()
				json_path.parent.mkdir(parents=True, exist_ok=True)

				# Merge with existing state if file exists
				merged_state = storage_state
				if json_path.exists():
					try:
						existing_state = json.loads(json_path.read_text())
						merged_state = self._merge_storage_states(existing_state, dict(storage_state))
					except Exception as e:
						self.logger.error(f'[StorageStateWatchdog] Failed to merge with existing state: {e}')

				# Write atomically
				temp_path = json_path.with_suffix('.json.tmp')
				temp_path.write_text(json.dumps(merged_state, indent=4, ensure_ascii=False), encoding='utf-8')

				# Backup existing file
				if json_path.exists():
					backup_path = json_path.with_suffix('.json.bak')
					json_path.replace(backup_path)

				# Move temp to final
				temp_path.replace(json_path)

				# Emit success event
				self.event_bus.dispatch(
					StorageStateSavedEvent(
						path=str(json_path),
						cookies_count=len(merged_state.get('cookies', [])),
						origins_count=len(merged_state.get('origins', [])),
					)
				)

				self.logger.debug(
					f'[StorageStateWatchdog] Saved storage state to {json_path} '
					f'({len(merged_state.get("cookies", []))} cookies, '
					f'{len(merged_state.get("origins", []))} origins)'
				)

			except Exception as e:
				self.logger.error(f'[StorageStateWatchdog] Failed to save storage state: {e}')