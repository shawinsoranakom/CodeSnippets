def _ensure_default_extensions_downloaded(self) -> list[str]:
		"""
		Ensure default extensions are downloaded and cached locally.
		Returns list of paths to extension directories.
		"""

		# Extension definitions - optimized for automation and content extraction
		# uBlock Origin Lite (ad blocking, MV3) + "I still don't care about cookies" (cookie banner handling)
		extensions = [
			{
				'name': 'uBlock Origin Lite',
				'id': 'ddkjiahejlhfcafbddmgiahcphecmpfh',
				'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=133&acceptformat=crx3&x=id%3Dddkjiahejlhfcafbddmgiahcphecmpfh%26uc',
			},
			{
				'name': "I still don't care about cookies",
				'id': 'edibdbjcniadpccecjdfdjjppcpchdlm',
				'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=133&acceptformat=crx3&x=id%3Dedibdbjcniadpccecjdfdjjppcpchdlm%26uc',
			},
			{
				'name': 'Force Background Tab',
				'id': 'gidlfommnbibbmegmgajdbikelkdcmcl',
				'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=133&acceptformat=crx3&x=id%3Dgidlfommnbibbmegmgajdbikelkdcmcl%26uc',
			},
			# {
			# 	'name': 'Captcha Solver: Auto captcha solving service',
			# 	'id': 'pgojnojmmhpofjgdmaebadhbocahppod',
			# 	'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130&acceptformat=crx3&x=id%3Dpgojnojmmhpofjgdmaebadhbocahppod%26uc',
			# },
			# Consent-O-Matic disabled - using uBlock Origin's cookie lists instead for simplicity
			# {
			# 	'name': 'Consent-O-Matic',
			# 	'id': 'mdjildafknihdffpkfmmpnpoiajfjnjd',
			# 	'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130&acceptformat=crx3&x=id%3Dmdjildafknihdffpkfmmpnpoiajfjnjd%26uc',
			# },
			# {
			# 	'name': 'Privacy | Protect Your Payments',
			# 	'id': 'hmgpakheknboplhmlicfkkgjipfabmhp',
			# 	'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130&acceptformat=crx3&x=id%3Dhmgpakheknboplhmlicfkkgjipfabmhp%26uc',
			# },
		]

		# Create extensions cache directory
		cache_dir = CONFIG.BROWSER_USE_EXTENSIONS_DIR
		cache_dir.mkdir(parents=True, exist_ok=True)
		# logger.debug(f'📁 Extensions cache directory: {_log_pretty_path(cache_dir)}')

		extension_paths = []
		loaded_extension_names = []

		for ext in extensions:
			ext_dir = cache_dir / ext['id']
			crx_file = cache_dir / f'{ext["id"]}.crx'

			# Check if extension is already extracted
			if ext_dir.exists() and (ext_dir / 'manifest.json').exists():
				if not self._check_extension_manifest_version(ext_dir, ext['name']):
					continue
				extension_paths.append(str(ext_dir))
				loaded_extension_names.append(ext['name'])
				continue

			try:
				# Download extension if not cached
				if not crx_file.exists():
					logger.info(f'📦 Downloading {ext["name"]} extension...')
					self._download_extension(ext['url'], crx_file)
				else:
					logger.debug(f'📦 Found cached {ext["name"]} .crx file')

				# Extract extension
				logger.info(f'📂 Extracting {ext["name"]} extension...')
				self._extract_extension(crx_file, ext_dir)

				if not self._check_extension_manifest_version(ext_dir, ext['name']):
					continue

				extension_paths.append(str(ext_dir))
				loaded_extension_names.append(ext['name'])

			except Exception as e:
				logger.warning(f'⚠️ Failed to setup {ext["name"]} extension: {e}')
				continue

		# Apply minimal patch to cookie extension with configurable whitelist
		for i, path in enumerate(extension_paths):
			if loaded_extension_names[i] == "I still don't care about cookies":
				self._apply_minimal_extension_patch(Path(path), self.cookie_whitelist_domains)

		if extension_paths:
			logger.debug(f'[BrowserProfile] 🧩 Extensions loaded ({len(extension_paths)}): [{", ".join(loaded_extension_names)}]')
		else:
			logger.warning('[BrowserProfile] ⚠️ No default extensions could be loaded')

		return extension_paths