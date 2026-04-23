def _fetch_single_catalog(self, entry: PresetCatalogEntry, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch a single catalog with per-URL caching.

        Args:
            entry: PresetCatalogEntry describing the catalog to fetch
            force_refresh: If True, bypass cache

        Returns:
            Catalog data dictionary

        Raises:
            PresetError: If catalog cannot be fetched
        """
        cache_file, metadata_file = self._get_cache_paths(entry.url)

        if not force_refresh and self._is_url_cache_valid(entry.url):
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                pass

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(entry.url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            if (
                "schema_version" not in catalog_data
                or "presets" not in catalog_data
            ):
                raise PresetError("Invalid preset catalog format")

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(catalog_data, indent=2))
            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": entry.url,
            }
            metadata_file.write_text(json.dumps(metadata, indent=2))

            return catalog_data

        except (ImportError, Exception) as e:
            if isinstance(e, PresetError):
                raise
            raise PresetError(
                f"Failed to fetch preset catalog from {entry.url}: {e}"
            )