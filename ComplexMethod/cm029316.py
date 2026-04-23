async def _execute_click_with_download_detection(
		self,
		click_coro,
		download_start_timeout: float = 0.5,
		download_complete_timeout: float = 30.0,
	) -> dict | None:
		"""Execute a click operation and automatically wait for any triggered download

		Args:
			click_coro: Coroutine that performs the click (should return click_metadata dict or None)
			download_start_timeout: Time to wait for download to start after click (seconds)
			download_complete_timeout: Time to wait for download to complete once started (seconds)

		Returns:
			Click metadata dict, potentially with 'download' key containing download info.
			If a download times out but is still in progress, includes 'download_in_progress' with status.
		"""
		import time

		download_started = asyncio.Event()
		download_completed = asyncio.Event()
		download_info: dict = {}
		progress_info: dict = {'last_update': 0.0, 'received_bytes': 0, 'total_bytes': 0, 'state': ''}

		def on_download_start(info: dict) -> None:
			"""Direct callback when download starts (called from CDP handler)."""
			if info.get('auto_download'):
				return  # ignore auto-downloads
			download_info['guid'] = info.get('guid', '')
			download_info['url'] = info.get('url', '')
			download_info['suggested_filename'] = info.get('suggested_filename', 'download')
			download_started.set()
			self.logger.debug(f'[ClickWithDownload] Download started: {download_info["suggested_filename"]}')

		def on_download_progress(info: dict) -> None:
			"""Direct callback when download progress updates (called from CDP handler)."""
			# Match by guid if available
			if download_info.get('guid') and info.get('guid') != download_info['guid']:
				return  # different download
			progress_info['last_update'] = time.time()
			progress_info['received_bytes'] = info.get('received_bytes', 0)
			progress_info['total_bytes'] = info.get('total_bytes', 0)
			progress_info['state'] = info.get('state', '')
			self.logger.debug(
				f'[ClickWithDownload] Progress: {progress_info["received_bytes"]}/{progress_info["total_bytes"]} bytes ({progress_info["state"]})'
			)

		def on_download_complete(info: dict) -> None:
			"""Direct callback when download completes (called from CDP handler)."""
			if info.get('auto_download'):
				return  # ignore auto-downloads
			# Match by guid if available, otherwise accept any non-auto download
			if download_info.get('guid') and info.get('guid') and info.get('guid') != download_info['guid']:
				return  # different download
			download_info['path'] = info.get('path', '')
			download_info['file_name'] = info.get('file_name', '')
			download_info['file_size'] = info.get('file_size', 0)
			download_info['file_type'] = info.get('file_type')
			download_info['mime_type'] = info.get('mime_type')
			download_completed.set()
			self.logger.debug(f'[ClickWithDownload] Download completed: {download_info["file_name"]}')

		# Get the downloads watchdog and register direct callbacks
		downloads_watchdog = self.browser_session._downloads_watchdog
		self.logger.debug(f'[ClickWithDownload] downloads_watchdog={downloads_watchdog is not None}')
		if downloads_watchdog:
			self.logger.debug('[ClickWithDownload] Registering download callbacks...')
			downloads_watchdog.register_download_callbacks(
				on_start=on_download_start,
				on_progress=on_download_progress,
				on_complete=on_download_complete,
			)
		else:
			self.logger.warning('[ClickWithDownload] No downloads_watchdog available!')

		try:
			# Perform the click
			click_metadata = await click_coro

			# Check for validation errors - return them immediately without waiting for downloads
			if isinstance(click_metadata, dict) and 'validation_error' in click_metadata:
				return click_metadata

			# Wait briefly to see if a download starts
			try:
				await asyncio.wait_for(download_started.wait(), timeout=download_start_timeout)

				# Download started!
				self.logger.info(f'📥 Download started: {download_info.get("suggested_filename", "unknown")}')

				# Now wait for it to complete with longer timeout
				try:
					await asyncio.wait_for(download_completed.wait(), timeout=download_complete_timeout)

					# Download completed successfully
					msg = f'Downloaded file: {download_info["file_name"]} ({download_info["file_size"]} bytes) saved to {download_info["path"]}'
					self.logger.info(f'💾 {msg}')

					# Merge download info into click_metadata
					if click_metadata is None:
						click_metadata = {}
					click_metadata['download'] = {
						'path': download_info['path'],
						'file_name': download_info['file_name'],
						'file_size': download_info['file_size'],
						'file_type': download_info.get('file_type'),
						'mime_type': download_info.get('mime_type'),
					}
				except TimeoutError:
					# Download timed out - check if it's still in progress
					if click_metadata is None:
						click_metadata = {}

					filename = download_info.get('suggested_filename', 'unknown')
					received = progress_info.get('received_bytes', 0)
					total = progress_info.get('total_bytes', 0)
					state = progress_info.get('state', 'unknown')
					last_update = progress_info.get('last_update', 0.0)
					time_since_update = time.time() - last_update if last_update > 0 else float('inf')

					# Check if download is still actively progressing (received update in last 5 seconds)
					is_still_active = time_since_update < 5.0 and state == 'inProgress'

					if is_still_active:
						# Download is still progressing - suggest waiting
						if total > 0:
							percent = (received / total) * 100
							progress_str = f'{percent:.1f}% ({received:,}/{total:,} bytes)'
						else:
							progress_str = f'{received:,} bytes downloaded (total size unknown)'

						msg = (
							f'Download timed out after {download_complete_timeout}s but is still in progress: '
							f'{filename} - {progress_str}. '
							f'The download appears to be progressing normally. Consider using the wait action '
							f'to allow more time for the download to complete.'
						)
						self.logger.warning(f'⏱️ {msg}')
						click_metadata['download_in_progress'] = {
							'file_name': filename,
							'received_bytes': received,
							'total_bytes': total,
							'state': state,
							'message': msg,
						}
					else:
						# Download may be stalled or completed
						if received > 0:
							msg = (
								f'Download timed out after {download_complete_timeout}s: {filename}. '
								f'Last progress: {received:,} bytes received. '
								f'The download may have stalled or completed - check the downloads folder.'
							)
						else:
							msg = (
								f'Download timed out after {download_complete_timeout}s: {filename}. '
								f'No progress data received - the download may have failed to start properly.'
							)
						self.logger.warning(f'⏱️ {msg}')
						click_metadata['download_timeout'] = {
							'file_name': filename,
							'received_bytes': received,
							'total_bytes': total,
							'message': msg,
						}
			except TimeoutError:
				# No download started within grace period
				pass

			return click_metadata if isinstance(click_metadata, dict) else None

		finally:
			# Unregister download callbacks
			if downloads_watchdog:
				downloads_watchdog.unregister_download_callbacks(
					on_start=on_download_start,
					on_progress=on_download_progress,
					on_complete=on_download_complete,
				)