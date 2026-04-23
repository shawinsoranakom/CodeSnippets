def on_response_received(event: ResponseReceivedEvent, session_id: str | None) -> None:
					"""Handle Network.responseReceived event to detect downloadable content.

					This callback is registered globally and uses session_id to determine the correct target.
					"""
					try:
						# Check if session_manager exists (may be None during browser shutdown)
						if not self.browser_session.session_manager:
							self.logger.warning('[DownloadsWatchdog] Session manager not found, skipping network monitoring')
							return

						# Look up target_id from session_id
						event_target_id = self.browser_session.session_manager.get_target_id_from_session_id(session_id)
						if not event_target_id:
							# Session not in pool - might be a stale session or not yet tracked
							return

						# Only process events for targets we're monitoring
						if event_target_id not in self._network_monitored_targets:
							return

						response = event.get('response', {})
						url = response.get('url', '')
						content_type = response.get('mimeType', '').lower()
						headers = {
							k.lower(): v for k, v in response.get('headers', {}).items()
						}  # Normalize for case-insensitive lookup
						request_type = event.get('type', '')

						# Skip non-HTTP URLs (data:, about:, chrome-extension:, etc.)
						if not url.startswith('http'):
							return

						# Skip fetch/XHR - real browsers don't download PDFs from programmatic requests
						if request_type in ('Fetch', 'XHR'):
							return

						# Check if it's a PDF
						is_pdf = 'application/pdf' in content_type

						# Check if it's marked as download via Content-Disposition header
						content_disposition = str(headers.get('content-disposition', '')).lower()
						is_download_attachment = 'attachment' in content_disposition

						# Filter out image/video/audio files even if marked as attachment
						# These are likely resources, not intentional downloads
						unwanted_content_types = [
							'image/',
							'video/',
							'audio/',
							'text/css',
							'text/javascript',
							'application/javascript',
							'application/x-javascript',
							'text/html',
							'application/json',
							'font/',
							'application/font',
							'application/x-font',
						]
						is_unwanted_type = any(content_type.startswith(prefix) for prefix in unwanted_content_types)
						if is_unwanted_type:
							return

						# Check URL extension to filter out obvious images/resources
						url_lower = url.lower().split('?')[0]  # Remove query params
						unwanted_extensions = [
							'.jpg',
							'.jpeg',
							'.png',
							'.gif',
							'.webp',
							'.svg',
							'.ico',
							'.css',
							'.js',
							'.woff',
							'.woff2',
							'.ttf',
							'.eot',
							'.mp4',
							'.webm',
							'.mp3',
							'.wav',
							'.ogg',
						]
						if any(url_lower.endswith(ext) for ext in unwanted_extensions):
							return

						# Only process if it's a PDF or download
						if not (is_pdf or is_download_attachment):
							return

						# If already downloaded this URL and file still exists, do nothing
						existing_path = self._session_pdf_urls.get(url)
						if existing_path:
							if os.path.exists(existing_path):
								return
							# Stale cache entry, allow re-download
							del self._session_pdf_urls[url]

						# Check if we've already processed this URL in this session
						if url in self._detected_downloads:
							self.logger.debug(f'[DownloadsWatchdog] Already detected download: {url[:80]}...')
							return

						# Mark as detected to avoid duplicates
						self._detected_downloads.add(url)

						# Extract filename from Content-Disposition if available
						suggested_filename = None
						if 'filename=' in content_disposition:
							# Parse filename from Content-Disposition header
							import re

							filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
							if filename_match:
								suggested_filename = filename_match.group(1).strip('\'"')

						self.logger.info(f'[DownloadsWatchdog] 🔍 Detected downloadable content via network: {url[:80]}...')
						self.logger.debug(
							f'[DownloadsWatchdog]   Content-Type: {content_type}, Is PDF: {is_pdf}, Is Attachment: {is_download_attachment}'
						)

						# Trigger download asynchronously in background (don't block event handler)
						async def download_in_background():
							# Don't permanently block re-processing this URL if download fails
							try:
								download_path = await self.download_file_from_url(
									url=url,
									target_id=event_target_id,  # Use target_id from session_id lookup
									content_type=content_type,
									suggested_filename=suggested_filename,
								)

								if download_path:
									self.logger.info(f'[DownloadsWatchdog] ✅ Successfully downloaded: {download_path}')
								else:
									self.logger.warning(f'[DownloadsWatchdog] ⚠️  Failed to download: {url[:80]}...')
							except Exception as e:
								self.logger.error(f'[DownloadsWatchdog] Error downloading in background: {type(e).__name__}: {e}')
							finally:
								# Allow future detections of the same URL
								self._detected_downloads.discard(url)

						# Create background task
						task = create_task_with_error_handling(
							download_in_background(),
							name='download_in_background',
							logger_instance=self.logger,
							suppress_exceptions=True,
						)
						self._cdp_event_tasks.add(task)
						task.add_done_callback(lambda t: self._cdp_event_tasks.discard(t))

					except Exception as e:
						self.logger.error(f'[DownloadsWatchdog] Error in network response handler: {type(e).__name__}: {e}')