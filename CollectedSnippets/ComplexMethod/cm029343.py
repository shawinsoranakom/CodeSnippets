async def _handle_download(self, download: Any) -> None:
		"""Handle a download event."""
		download_id = f'{id(download)}'
		self._active_downloads[download_id] = download
		self.logger.debug(f'[DownloadsWatchdog] ⬇️ Handling download: {download.suggested_filename} from {download.url[:100]}...')

		# Debug: Check if download is already being handled elsewhere
		failure = (
			await download.failure()
		)  # TODO: it always fails for some reason, figure out why connect_over_cdp makes accept_downloads not work
		self.logger.warning(f'[DownloadsWatchdog] ❌ Download state - canceled: {failure}, url: {download.url}')
		# logger.info(f'[DownloadsWatchdog] Active downloads count: {len(self._active_downloads)}')

		try:
			current_step = 'getting_download_info'
			# Get download info immediately
			url = download.url
			suggested_filename = download.suggested_filename

			current_step = 'determining_download_directory'
			# Determine download directory from browser profile
			downloads_dir = self.browser_session.browser_profile.downloads_path
			if not downloads_dir:
				downloads_dir = str(Path.home() / 'Downloads')
			else:
				downloads_dir = str(downloads_dir)  # Ensure it's a string

			# Check if Playwright already auto-downloaded the file (due to CDP setup)
			original_path = Path(downloads_dir) / suggested_filename
			if original_path.exists() and original_path.stat().st_size > 0:
				self.logger.debug(
					f'[DownloadsWatchdog] File already downloaded by Playwright: {original_path} ({original_path.stat().st_size} bytes)'
				)

				# Use the existing file instead of creating a duplicate
				download_path = original_path
				file_size = original_path.stat().st_size
				unique_filename = suggested_filename
			else:
				current_step = 'generating_unique_filename'
				# Ensure unique filename
				unique_filename = await self._get_unique_filename(downloads_dir, suggested_filename)
				download_path = Path(downloads_dir) / unique_filename

				self.logger.debug(f'[DownloadsWatchdog] Download started: {unique_filename} from {url[:100]}...')

				current_step = 'calling_save_as'
				# Save the download using Playwright's save_as method
				self.logger.debug(f'[DownloadsWatchdog] Saving download to: {download_path}')
				self.logger.debug(f'[DownloadsWatchdog] Download path exists: {download_path.parent.exists()}')
				self.logger.debug(f'[DownloadsWatchdog] Download path writable: {os.access(download_path.parent, os.W_OK)}')

				try:
					self.logger.debug('[DownloadsWatchdog] About to call download.save_as()...')
					await download.save_as(str(download_path))
					self.logger.debug(f'[DownloadsWatchdog] Successfully saved download to: {download_path}')
					current_step = 'save_as_completed'
				except Exception as save_error:
					self.logger.error(f'[DownloadsWatchdog] save_as() failed with error: {save_error}')
					raise save_error

				# Get file info
				file_size = download_path.stat().st_size if download_path.exists() else 0

			# Determine file type from extension
			file_ext = download_path.suffix.lower().lstrip('.')
			file_type = file_ext if file_ext else None

			# Try to get MIME type from response headers if available
			mime_type = None
			# Note: Playwright doesn't expose response headers directly from Download object

			# Check if this was a PDF auto-download
			auto_download = False
			if file_type == 'pdf':
				auto_download = self._is_auto_download_enabled()

			# Emit download event
			self.event_bus.dispatch(
				FileDownloadedEvent(
					url=url,
					path=str(download_path),
					file_name=suggested_filename,
					file_size=file_size,
					file_type=file_type,
					mime_type=mime_type,
					from_cache=False,
					auto_download=auto_download,
				)
			)

			self.logger.debug(
				f'[DownloadsWatchdog] ✅ Download completed: {suggested_filename} ({file_size} bytes) saved to {download_path}'
			)

			# File is now tracked on filesystem, no need to track in memory

		except Exception as e:
			self.logger.error(
				f'[DownloadsWatchdog] Error handling download at step "{locals().get("current_step", "unknown")}", error: {e}'
			)
			self.logger.error(
				f'[DownloadsWatchdog] Download state - URL: {download.url}, filename: {download.suggested_filename}'
			)
		finally:
			# Clean up tracking
			if download_id in self._active_downloads:
				del self._active_downloads[download_id]