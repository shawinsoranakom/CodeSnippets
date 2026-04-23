def _copy_profile(self) -> None:
		"""Copy profile to temp directory if user_data_dir is not None and not already a temp dir."""
		if self.user_data_dir is None:
			return

		user_data_str = str(self.user_data_dir)
		if 'browser-use-user-data-dir-' in user_data_str.lower():
			# Already using a temp directory, no need to copy
			return

		is_chrome = (
			'chrome' in user_data_str.lower()
			or ('chrome' in str(self.executable_path).lower())
			or self.channel
			in (BrowserChannel.CHROME, BrowserChannel.CHROME_BETA, BrowserChannel.CHROME_DEV, BrowserChannel.CHROME_CANARY)
		)

		if not is_chrome:
			return

		temp_dir = tempfile.mkdtemp(prefix='browser-use-user-data-dir-')
		path_original_user_data = Path(self.user_data_dir)
		path_original_profile = path_original_user_data / self.profile_directory
		path_temp_profile = Path(temp_dir) / self.profile_directory

		if path_original_profile.exists():
			import shutil

			shutil.copytree(path_original_profile, path_temp_profile)
			local_state_src = path_original_user_data / 'Local State'
			local_state_dst = Path(temp_dir) / 'Local State'
			if local_state_src.exists():
				shutil.copy(local_state_src, local_state_dst)
			logger.info(f'Copied profile ({self.profile_directory}) and Local State to temp directory: {temp_dir}')

		else:
			Path(temp_dir).mkdir(parents=True, exist_ok=True)
			path_temp_profile.mkdir(parents=True, exist_ok=True)
			logger.info(f'Created new profile ({self.profile_directory}) in temp directory: {temp_dir}')

		self.user_data_dir = temp_dir