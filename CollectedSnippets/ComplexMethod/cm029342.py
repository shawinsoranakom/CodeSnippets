async def _handle_cdp_download(
		self, event: DownloadWillBeginEvent, target_id: TargetID, session_id: SessionID | None
	) -> None:
		"""Handle a CDP Page.downloadWillBegin event."""
		downloads_dir = (
			Path(
				self.browser_session.browser_profile.downloads_path
				or f'{tempfile.gettempdir()}/browser_use_downloads.{str(self.browser_session.id)[-4:]}'
			)
			.expanduser()
			.resolve()
		)  # Ensure path is properly expanded

		# Initialize variables that may be used outside try blocks
		unique_filename = None
		file_size = 0
		expected_path = None
		download_result = None
		download_url = event.get('url', '')
		suggested_filename = event.get('suggestedFilename', 'download')
		guid = event.get('guid', '')

		try:
			self.logger.debug(f'[DownloadsWatchdog] ⬇️ File download starting: {suggested_filename} from {download_url[:100]}...')
			self.logger.debug(f'[DownloadsWatchdog] Full CDP event: {event}')

			# Since Browser.setDownloadBehavior is already configured, the browser will download the file
			# We just need to wait for it to appear in the downloads directory
			expected_path = downloads_dir / suggested_filename

			# For remote browsers, don't poll local filesystem; downloadProgress handler will emit the event
			if not self.browser_session.is_local:
				return
		except Exception as e:
			self.logger.error(f'[DownloadsWatchdog] ❌ Error handling CDP download: {type(e).__name__} {e}')

		# If we reach here, the fetch method failed, so wait for native download
		# Poll the downloads directory for new files
		self.logger.debug(f'[DownloadsWatchdog] Checking if browser auto-download saved the file for us: {suggested_filename}')

		# Poll for new files
		max_wait = 20  # seconds
		start_time = asyncio.get_event_loop().time()

		while asyncio.get_event_loop().time() - start_time < max_wait:  # noqa: ASYNC110
			await asyncio.sleep(5.0)  # Check every 5 seconds

			if Path(downloads_dir).exists():
				for file_path in Path(downloads_dir).iterdir():
					# Skip hidden files and files that were already there
					if (
						file_path.is_file()
						and not file_path.name.startswith('.')
						and file_path.name not in self._initial_downloads_snapshot
					):
						# Add to snapshot immediately to prevent duplicate detection
						self._initial_downloads_snapshot.add(file_path.name)
						# Check if file has content (> 4 bytes)
						try:
							file_size = file_path.stat().st_size
							if file_size > 4:
								# Found a new download!
								self.logger.debug(
									f'[DownloadsWatchdog] ✅ Found downloaded file: {file_path} ({file_size} bytes)'
								)

								# Determine file type from extension
								file_ext = file_path.suffix.lower().lstrip('.')
								file_type = file_ext if file_ext else None

								# Dispatch download event
								# Skip if already handled by progress/JS fetch
								info = self._cdp_downloads_info.get(guid, {})
								if info.get('handled'):
									return
								self.event_bus.dispatch(
									FileDownloadedEvent(
										guid=guid,
										url=download_url,
										path=str(file_path),
										file_name=file_path.name,
										file_size=file_size,
										file_type=file_type,
									)
								)
							# Mark as handled after dispatch
							try:
								if guid in self._cdp_downloads_info:
									self._cdp_downloads_info[guid]['handled'] = True
							except (KeyError, AttributeError):
								pass
							return
						except Exception as e:
							self.logger.debug(f'[DownloadsWatchdog] Error checking file {file_path}: {e}')

		self.logger.warning(f'[DownloadsWatchdog] Download did not complete within {max_wait} seconds')