def download_progress_handler(event: CDPDownloadProgressEvent, session_id: SessionID | None) -> None:
			guid = event.get('guid', '')
			state = event.get('state', '')
			received_bytes = int(event.get('receivedBytes', 0))
			total_bytes = int(event.get('totalBytes', 0))

			# Call direct callbacks first (for click handlers tracking progress)
			progress_info = {
				'guid': guid,
				'received_bytes': received_bytes,
				'total_bytes': total_bytes,
				'state': state,
			}
			for callback in self._download_progress_callbacks:
				try:
					callback(progress_info)
				except Exception as e:
					self.logger.debug(f'[DownloadsWatchdog] Error in download progress callback: {e}')

			# Emit progress event for all states so listeners can track progress
			from browser_use.browser.events import DownloadProgressEvent as DownloadProgressEventInternal

			self.event_bus.dispatch(
				DownloadProgressEventInternal(
					guid=guid,
					received_bytes=received_bytes,
					total_bytes=total_bytes,
					state=state,
				)
			)

			# Check if download is complete
			if state == 'completed':
				file_path = event.get('filePath')
				if self.browser_session.is_local:
					if file_path:
						self.logger.debug(f'[DownloadsWatchdog] Download completed: {file_path}')
						# Track the download
						self._track_download(file_path, guid=guid)
						# Mark as handled to prevent fallback duplicate dispatch
						try:
							if guid in self._cdp_downloads_info:
								self._cdp_downloads_info[guid]['handled'] = True
						except (KeyError, AttributeError):
							pass
					else:
						# No filePath provided - detect by comparing with initial snapshot
						self.logger.debug('[DownloadsWatchdog] No filePath in progress event; detecting via filesystem')
						downloads_path = self.browser_session.browser_profile.downloads_path
						if downloads_path:
							downloads_dir = Path(downloads_path).expanduser().resolve()
							if downloads_dir.exists():
								for f in downloads_dir.iterdir():
									if (
										f.is_file()
										and not f.name.startswith('.')
										and f.name not in self._initial_downloads_snapshot
									):
										# Check file has content before processing
										if f.stat().st_size > 4:
											# Found a new file! Add to snapshot immediately to prevent duplicate detection
											self._initial_downloads_snapshot.add(f.name)
											self.logger.debug(f'[DownloadsWatchdog] Detected new download: {f.name}')
											self._track_download(str(f))
											# Mark as handled
											try:
												if guid in self._cdp_downloads_info:
													self._cdp_downloads_info[guid]['handled'] = True
											except (KeyError, AttributeError):
												pass
											break
				else:
					# Remote browser: do not touch local filesystem. Fallback to downloadPath+suggestedFilename
					info = self._cdp_downloads_info.get(guid, {})
					try:
						suggested_filename = info.get('suggested_filename') or (Path(file_path).name if file_path else 'download')
						downloads_path = str(self.browser_session.browser_profile.downloads_path or '')
						effective_path = file_path or str(Path(downloads_path) / suggested_filename)
						file_name = Path(effective_path).name
						file_ext = Path(file_name).suffix.lower().lstrip('.')
						self.event_bus.dispatch(
							FileDownloadedEvent(
								guid=guid,
								url=info.get('url', ''),
								path=str(effective_path),
								file_name=file_name,
								file_size=0,
								file_type=file_ext if file_ext else None,
							)
						)
						self.logger.debug(f'[DownloadsWatchdog] ✅ (remote) Download completed: {effective_path}')
					finally:
						if guid in self._cdp_downloads_info:
							del self._cdp_downloads_info[guid]