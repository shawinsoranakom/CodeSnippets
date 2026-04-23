def _fetch_single_catalog(self, entry: CatalogEntry, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch a single catalog with per-URL caching.

        For the DEFAULT_CATALOG_URL, uses legacy cache files (self.cache_file /
        self.cache_metadata_file) for backward compatibility. For all other URLs,
        uses URL-hash-based cache files in self.cache_dir.

        Args:
            entry: CatalogEntry describing the catalog to fetch
            force_refresh: If True, bypass cache

        Returns:
            Catalog data dictionary

        Raises:
            ExtensionError: If catalog cannot be fetched or has invalid format
        """
        import urllib.request
        import urllib.error

        # Determine cache file paths (backward compat for default catalog)
        if entry.url == self.DEFAULT_CATALOG_URL:
            cache_file = self.cache_file
            cache_meta_file = self.cache_metadata_file
            is_valid = not force_refresh and self.is_cache_valid()
        else:
            url_hash = hashlib.sha256(entry.url.encode()).hexdigest()[:16]
            cache_file = self.cache_dir / f"catalog-{url_hash}.json"
            cache_meta_file = self.cache_dir / f"catalog-{url_hash}-metadata.json"
            is_valid = False
            if not force_refresh and cache_file.exists() and cache_meta_file.exists():
                try:
                    metadata = json.loads(cache_meta_file.read_text())
                    cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
                    if cached_at.tzinfo is None:
                        cached_at = cached_at.replace(tzinfo=timezone.utc)
                    age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                    is_valid = age < self.CACHE_DURATION
                except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                    # If metadata is invalid or missing expected fields, treat cache as invalid
                    pass

        # Use cache if valid
        if is_valid:
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                pass

        # Fetch from network
        try:
            with urllib.request.urlopen(entry.url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            if "schema_version" not in catalog_data or "extensions" not in catalog_data:
                raise ExtensionError(f"Invalid catalog format from {entry.url}")

            # Save to cache
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(catalog_data, indent=2))
            cache_meta_file.write_text(json.dumps({
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": entry.url,
            }, indent=2))

            return catalog_data

        except urllib.error.URLError as e:
            raise ExtensionError(f"Failed to fetch catalog from {entry.url}: {e}")
        except json.JSONDecodeError as e:
            raise ExtensionError(f"Invalid JSON in catalog from {entry.url}: {e}")