def _fetch_single_catalog(
        self,
        entry: IntegrationCatalogEntry,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Fetch one catalog, with per-URL caching."""
        import urllib.error
        import urllib.request

        url_hash = hashlib.sha256(entry.url.encode()).hexdigest()[:16]
        cache_file = self.cache_dir / f"catalog-{url_hash}.json"
        cache_meta = self.cache_dir / f"catalog-{url_hash}-metadata.json"

        if not force_refresh and cache_file.exists() and cache_meta.exists():
            try:
                meta = json.loads(cache_meta.read_text(encoding="utf-8"))
                cached_at = datetime.fromisoformat(meta.get("cached_at", ""))
                if cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if age < self.CACHE_DURATION:
                    return json.loads(cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError, OSError, UnicodeError):
                # Cache is invalid or stale metadata; delete and refetch from source.
                try:
                    cache_file.unlink(missing_ok=True)
                    cache_meta.unlink(missing_ok=True)
                except OSError:
                    pass  # Cache cleanup is best-effort; ignore deletion failures.

        try:
            with urllib.request.urlopen(entry.url, timeout=10) as resp:
                # Validate final URL after redirects
                final_url = resp.geturl()
                if final_url != entry.url:
                    self._validate_catalog_url(final_url)
                catalog_data = json.loads(resp.read())

            if not isinstance(catalog_data, dict):
                raise IntegrationCatalogError(
                    f"Invalid catalog format from {entry.url}: expected a JSON object"
                )
            if (
                "schema_version" not in catalog_data
                or "integrations" not in catalog_data
            ):
                raise IntegrationCatalogError(
                    f"Invalid catalog format from {entry.url}"
                )
            if not isinstance(catalog_data.get("integrations"), dict):
                raise IntegrationCatalogError(
                    f"Invalid catalog format from {entry.url}: 'integrations' must be a JSON object"
                )

            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")
                cache_meta.write_text(
                    json.dumps(
                        {
                            "cached_at": datetime.now(timezone.utc).isoformat(),
                            "catalog_url": entry.url,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass  # Cache is best-effort; proceed with fetched data
            return catalog_data

        except urllib.error.URLError as exc:
            raise IntegrationCatalogError(
                f"Failed to fetch catalog from {entry.url}: {exc}"
            )
        except json.JSONDecodeError as exc:
            raise IntegrationCatalogError(
                f"Invalid JSON in catalog from {entry.url}: {exc}"
            )