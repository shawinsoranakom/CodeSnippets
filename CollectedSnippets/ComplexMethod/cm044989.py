def fetch_catalog(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch extension catalog from URL or cache.

        Args:
            force_refresh: If True, bypass cache and fetch from network

        Returns:
            Catalog data dictionary

        Raises:
            ExtensionError: If catalog cannot be fetched
        """
        # Check cache first unless force refresh
        if not force_refresh and self.is_cache_valid():
            try:
                return json.loads(self.cache_file.read_text())
            except json.JSONDecodeError:
                pass  # Fall through to network fetch

        # Fetch from network
        catalog_url = self.get_catalog_url()

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            # Validate catalog structure
            if "schema_version" not in catalog_data or "extensions" not in catalog_data:
                raise ExtensionError("Invalid catalog format")

            # Save to cache
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(catalog_data, indent=2))

            # Save cache metadata
            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": catalog_url,
            }
            self.cache_metadata_file.write_text(json.dumps(metadata, indent=2))

            return catalog_data

        except urllib.error.URLError as e:
            raise ExtensionError(f"Failed to fetch catalog from {catalog_url}: {e}")
        except json.JSONDecodeError as e:
            raise ExtensionError(f"Invalid JSON in catalog: {e}")