def get_args(self) -> list[str]:
		"""Get the list of all Chrome CLI launch args for this profile (compiled from defaults, user-provided, and system-specific)."""

		if isinstance(self.ignore_default_args, list):
			default_args = set(CHROME_DEFAULT_ARGS) - set(self.ignore_default_args)
		elif self.ignore_default_args is True:
			default_args = []
		elif not self.ignore_default_args:
			default_args = CHROME_DEFAULT_ARGS

		assert self.user_data_dir is not None, 'user_data_dir must be set to a non-default path'

		# Capture args before conversion for logging
		pre_conversion_args = [
			*default_args,
			*self.args,
			f'--user-data-dir={self.user_data_dir}',
			f'--profile-directory={self.profile_directory}',
			*(CHROME_DOCKER_ARGS if (CONFIG.IN_DOCKER or not self.chromium_sandbox) else []),
			*(CHROME_HEADLESS_ARGS if self.headless else []),
			*(CHROME_DISABLE_SECURITY_ARGS if self.disable_security else []),
			*(CHROME_DETERMINISTIC_RENDERING_ARGS if self.deterministic_rendering else []),
			*(
				[f'--window-size={self.window_size["width"]},{self.window_size["height"]}']
				if self.window_size
				else (['--start-maximized'] if not self.headless else [])
			),
			*(
				[f'--window-position={self.window_position["width"]},{self.window_position["height"]}']
				if self.window_position
				else []
			),
			*(self._get_extension_args() if self.enable_default_extensions else []),
		]

		# Proxy flags
		proxy_server = self.proxy.server if self.proxy else None
		proxy_bypass = self.proxy.bypass if self.proxy else None

		if proxy_server:
			pre_conversion_args.append(f'--proxy-server={proxy_server}')
			if proxy_bypass:
				pre_conversion_args.append(f'--proxy-bypass-list={proxy_bypass}')

		# User agent flag
		if self.user_agent:
			pre_conversion_args.append(f'--user-agent={self.user_agent}')

		# Special handling for --disable-features to merge values instead of overwriting
		# This prevents disable_security=True from breaking extensions by ensuring
		# both default features (including extension-related) and security features are preserved
		disable_features_values = []
		non_disable_features_args = []

		# Extract and merge all --disable-features values
		for arg in pre_conversion_args:
			if arg.startswith('--disable-features='):
				features = arg.split('=', 1)[1]
				disable_features_values.extend(features.split(','))
			else:
				non_disable_features_args.append(arg)

		# Remove duplicates while preserving order
		if disable_features_values:
			unique_features = []
			seen = set()
			for feature in disable_features_values:
				feature = feature.strip()
				if feature and feature not in seen:
					unique_features.append(feature)
					seen.add(feature)

			# Add merged disable-features back
			non_disable_features_args.append(f'--disable-features={",".join(unique_features)}')

		# convert to dict and back to dedupe and merge other duplicate args
		final_args_list = BrowserLaunchArgs.args_as_list(BrowserLaunchArgs.args_as_dict(non_disable_features_args))

		return final_args_list