def _fetch_single_catalog(
        self, entry: WorkflowCatalogEntry, force_refresh: bool = False
    ) -> dict[str, Any]:
        """Fetch a single catalog, using cache when possible."""
        cache_file, meta_file = self._get_cache_paths(entry.url)

        if not force_refresh and self._is_url_cache_valid(entry.url):
            try:
                with open(cache_file, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Fetch from URL — validate scheme before opening and after redirects
        from urllib.parse import urlparse
        from urllib.request import urlopen

        def _validate_catalog_url(url: str) -> None:
            parsed = urlparse(url)
            is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if parsed.scheme != "https" and not (
                parsed.scheme == "http" and is_localhost
            ):
                raise WorkflowCatalogError(
                    f"Refusing to fetch catalog from non-HTTPS URL: {url}"
                )

        _validate_catalog_url(entry.url)

        try:
            with urlopen(entry.url, timeout=30) as resp:  # noqa: S310
                _validate_catalog_url(resp.geturl())
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            # Fall back to cache if available
            if cache_file.exists():
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, ValueError, OSError):
                    pass
            raise WorkflowCatalogError(
                f"Failed to fetch catalog from {entry.url}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise WorkflowCatalogError(
                f"Catalog from {entry.url} is not a valid JSON object."
            )

        # Write cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({"url": entry.url, "fetched_at": time.time()}, f)

        return data