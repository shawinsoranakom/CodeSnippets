async def download_file_from_url(
		self, url: str, target_id: TargetID, content_type: str | None = None, suggested_filename: str | None = None
	) -> str | None:
		"""Generic method to download any file from a URL.

		Args:
			url: The URL to download
			target_id: The target ID for CDP session
			content_type: Optional content type (e.g., 'application/pdf')
			suggested_filename: Optional filename from Content-Disposition header

		Returns:
			Path to downloaded file, or None if download failed
		"""
		if not self.browser_session.browser_profile.downloads_path:
			self.logger.warning('[DownloadsWatchdog] No downloads path configured')
			return None

		# Check if already downloaded in this session
		if url in self._session_pdf_urls:
			existing_path = self._session_pdf_urls[url]
			if os.path.exists(existing_path):
				self.logger.debug(f'[DownloadsWatchdog] File already downloaded in session: {existing_path}')
				return existing_path

			# Stale cache entry: the file was removed/cleaned up after we cached it.
			self.logger.debug(f'[DownloadsWatchdog] Cached download path no longer exists, re-downloading: {existing_path}')
			del self._session_pdf_urls[url]

		try:
			# Get or create CDP session for this target
			temp_session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)

			# Determine filename
			if suggested_filename:
				filename = suggested_filename
			else:
				# Extract from URL
				filename = os.path.basename(url.split('?')[0])  # Remove query params
				if not filename or '.' not in filename:
					# Fallback: use content type to determine extension
					if content_type and 'pdf' in content_type:
						filename = 'document.pdf'
					else:
						filename = 'download'

			# Ensure downloads directory exists
			downloads_dir = str(self.browser_session.browser_profile.downloads_path)
			os.makedirs(downloads_dir, exist_ok=True)

			# Generate unique filename if file exists
			final_filename = filename
			existing_files = os.listdir(downloads_dir)
			if filename in existing_files:
				base, ext = os.path.splitext(filename)
				counter = 1
				while f'{base} ({counter}){ext}' in existing_files:
					counter += 1
				final_filename = f'{base} ({counter}){ext}'
				self.logger.debug(f'[DownloadsWatchdog] File exists, using: {final_filename}')

			self.logger.debug(f'[DownloadsWatchdog] Downloading from: {url[:100]}...')

			# Download using JavaScript fetch to leverage browser cache
			escaped_url = json.dumps(url)

			result = await asyncio.wait_for(
				temp_session.cdp_client.send.Runtime.evaluate(
					params={
						'expression': f"""
				(async () => {{
					try {{
						const response = await fetch({escaped_url}, {{
							cache: 'force-cache'
						}});
						if (!response.ok) {{
							throw new Error(`HTTP error! status: ${{response.status}}`);
						}}
						const blob = await response.blob();
						const arrayBuffer = await blob.arrayBuffer();
						const uint8Array = new Uint8Array(arrayBuffer);

						return {{
							data: Array.from(uint8Array),
							responseSize: uint8Array.length
						}};
					}} catch (error) {{
						throw new Error(`Fetch failed: ${{error.message}}`);
					}}
				}})()
				""",
						'awaitPromise': True,
						'returnByValue': True,
					},
					session_id=temp_session.session_id,
				),
				timeout=15.0,  # 15 second timeout
			)

			download_result = result.get('result', {}).get('value', {})

			if download_result and download_result.get('data') and len(download_result['data']) > 0:
				download_path = os.path.join(downloads_dir, final_filename)

				# Save the file asynchronously
				async with await anyio.open_file(download_path, 'wb') as f:
					await f.write(bytes(download_result['data']))

				# Verify file was written successfully
				if os.path.exists(download_path):
					actual_size = os.path.getsize(download_path)
					self.logger.debug(f'[DownloadsWatchdog] File written: {download_path} ({actual_size} bytes)')

					# Determine file type
					file_ext = Path(final_filename).suffix.lower().lstrip('.')
					mime_type = content_type or f'application/{file_ext}'

					# Store URL->path mapping for this session
					self._session_pdf_urls[url] = download_path

					# Emit file downloaded event
					self.logger.debug(f'[DownloadsWatchdog] Dispatching FileDownloadedEvent for {final_filename}')
					self.event_bus.dispatch(
						FileDownloadedEvent(
							url=url,
							path=download_path,
							file_name=final_filename,
							file_size=actual_size,
							file_type=file_ext if file_ext else None,
							mime_type=mime_type,
							auto_download=True,
						)
					)

					return download_path
				else:
					self.logger.error(f'[DownloadsWatchdog] Failed to write file: {download_path}')
					return None
			else:
				self.logger.warning(f'[DownloadsWatchdog] No data received when downloading from {url}')
				return None

		except TimeoutError:
			self.logger.warning(f'[DownloadsWatchdog] Download timed out: {url[:80]}...')
			return None
		except Exception as e:
			self.logger.warning(f'[DownloadsWatchdog] Download failed: {type(e).__name__}: {e}')
			return None