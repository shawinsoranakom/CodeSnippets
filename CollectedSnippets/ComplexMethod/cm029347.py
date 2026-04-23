async def _launch_browser(self, max_retries: int = 3) -> tuple[psutil.Process, str]:
		"""Launch browser process and return (process, cdp_url).

		Handles launch errors by falling back to temporary directories if needed.

		Returns:
			Tuple of (psutil.Process, cdp_url)
		"""
		# Keep track of original user_data_dir to restore if needed
		profile = self.browser_session.browser_profile
		self._original_user_data_dir = str(profile.user_data_dir) if profile.user_data_dir else None
		self._temp_dirs_to_cleanup = []

		for attempt in range(max_retries):
			try:
				# Get launch args from profile
				launch_args = profile.get_args()

				# Add debugging port
				debug_port = self._find_free_port()
				launch_args.extend(
					[
						f'--remote-debugging-port={debug_port}',
					]
				)
				assert '--user-data-dir' in str(launch_args), (
					'User data dir must be set somewhere in launch args to a non-default path, otherwise Chrome will not let us attach via CDP'
				)

				# Get browser executable
				# Priority: custom executable > fallback paths > playwright subprocess
				if profile.executable_path:
					browser_path = profile.executable_path
					self.logger.debug(f'[LocalBrowserWatchdog] 📦 Using custom local browser executable_path= {browser_path}')
				else:
					# self.logger.debug('[LocalBrowserWatchdog] 🔍 Looking for local browser binary path...')
					# Try fallback paths first (Playwright's Chromium preferred by default)
					browser_path = self._find_installed_browser_path(channel=profile.channel)
					if not browser_path:
						self.logger.error(
							'[LocalBrowserWatchdog] ⚠️ No local browser binary found, installing browser using playwright subprocess...'
						)
						browser_path = await self._install_browser_with_playwright()

				self.logger.debug(f'[LocalBrowserWatchdog] 📦 Found local browser installed at executable_path= {browser_path}')
				if not browser_path:
					raise RuntimeError('No local Chrome/Chromium install found, and failed to install with playwright')

				# Launch browser subprocess directly
				self.logger.debug(f'[LocalBrowserWatchdog] 🚀 Launching browser subprocess with {len(launch_args)} args...')
				self.logger.debug(
					f'[LocalBrowserWatchdog] 📂 user_data_dir={profile.user_data_dir}, profile_directory={profile.profile_directory}'
				)
				subprocess = await asyncio.create_subprocess_exec(
					browser_path,
					*launch_args,
					stdout=asyncio.subprocess.PIPE,
					stderr=asyncio.subprocess.PIPE,
				)
				self.logger.debug(
					f'[LocalBrowserWatchdog] 🎭 Browser running with browser_pid= {subprocess.pid} 🔗 listening on CDP port :{debug_port}'
				)

				# Convert to psutil.Process
				process = psutil.Process(subprocess.pid)

				# Wait for CDP to be ready and get the URL
				cdp_url = await self._wait_for_cdp_url(debug_port)

				# Success! Clean up only the temp dirs we created but didn't use
				currently_used_dir = str(profile.user_data_dir)
				unused_temp_dirs = [tmp_dir for tmp_dir in self._temp_dirs_to_cleanup if str(tmp_dir) != currently_used_dir]

				for tmp_dir in unused_temp_dirs:
					try:
						shutil.rmtree(tmp_dir, ignore_errors=True)
					except Exception:
						pass

				# Keep only the in-use directory for cleanup during browser kill
				if currently_used_dir and 'browseruse-tmp-' in currently_used_dir:
					self._temp_dirs_to_cleanup = [Path(currently_used_dir)]
				else:
					self._temp_dirs_to_cleanup = []

				return process, cdp_url

			except Exception as e:
				error_str = str(e).lower()

				# Check if this is a user_data_dir related error
				if any(err in error_str for err in ['singletonlock', 'user data directory', 'cannot create', 'already in use']):
					self.logger.warning(f'Browser launch failed (attempt {attempt + 1}/{max_retries}): {e}')

					if attempt < max_retries - 1:
						# Create a temporary directory for next attempt
						tmp_dir = Path(tempfile.mkdtemp(prefix='browseruse-tmp-'))
						self._temp_dirs_to_cleanup.append(tmp_dir)

						# Update profile to use temp directory
						profile.user_data_dir = str(tmp_dir)
						self.logger.debug(f'Retrying with temporary user_data_dir: {tmp_dir}')

						# Small delay before retry
						await asyncio.sleep(0.5)
						continue

				# Not a recoverable error or last attempt failed
				# Restore original user_data_dir before raising
				if self._original_user_data_dir is not None:
					profile.user_data_dir = self._original_user_data_dir

				# Clean up any temp dirs we created
				for tmp_dir in self._temp_dirs_to_cleanup:
					try:
						shutil.rmtree(tmp_dir, ignore_errors=True)
					except Exception:
						pass

				raise

		# Should not reach here, but just in case
		if self._original_user_data_dir is not None:
			profile.user_data_dir = self._original_user_data_dir
		raise RuntimeError(f'Failed to launch browser after {max_retries} attempts')