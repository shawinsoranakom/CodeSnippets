def fetch_catalog(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch preset catalog from URL or cache.

        Args:
            force_refresh: If True, bypass cache and fetch from network

        Returns:
            Catalog data dictionary

        Raises:
            PresetError: If catalog cannot be fetched
        """
        catalog_url = self.get_catalog_url()

        if not force_refresh and self.is_cache_valid():
            try:
                metadata = json.loads(self.cache_metadata_file.read_text())
                if metadata.get("catalog_url") == catalog_url:
                    return json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, OSError):
                # Cache is corrupt or unreadable; fall through to network fetch
                pass

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            if (
                "schema_version" not in catalog_data
                or "presets" not in catalog_data
            ):
                raise PresetError("Invalid preset catalog format")

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(catalog_data, indent=2))

            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": catalog_url,
            }
            self.cache_metadata_file.write_text(
                json.dumps(metadata, indent=2)
            )

            return catalog_data

        except (ImportError, Exception) as e:
            if isinstance(e, PresetError):
                raise
            raise PresetError(
                f"Failed to fetch preset catalog from {catalog_url}: {e}"
            )