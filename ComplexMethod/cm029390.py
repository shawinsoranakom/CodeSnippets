async def clean_old_caches(self, keep_count: int = 3) -> None:
		"""Clean up old cache files, keeping only the most recent ones from this source URL"""
		try:
			# List all JSON files in the cache directory
			cache_files = list(self._cache_dir.glob('*.json'))

			if not cache_files:
				return

			# Only consider cache files from the same source URL
			own_files: list[Path] = []
			for cache_file in cache_files:
				try:
					cached = CachedPricingData.model_validate_json(cache_file.read_text())
					if self._cache_source_matches(cached):
						own_files.append(cache_file)
				except Exception:
					pass

			if len(own_files) <= keep_count:
				return

			# Sort by modification time (oldest first)
			own_files.sort(key=lambda f: f.stat().st_mtime)

			# Remove all but the most recent files
			for cache_file in own_files[:-keep_count]:
				try:
					os.remove(cache_file)
				except Exception:
					pass
		except Exception as e:
			logger.debug(f'Error cleaning old cache files: {e}')