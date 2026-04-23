def _load_catalog_config(
        self, config_path: Path
    ) -> Optional[List[IntegrationCatalogEntry]]:
        """Load catalog stack from a YAML file.

        Returns None when the file does not exist.

        Raises:
            IntegrationCatalogError: on invalid content
        """
        if not config_path.exists():
            return None
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError, UnicodeError) as exc:
            raise IntegrationCatalogError(
                f"Failed to read catalog config {config_path}: {exc}"
            )
        if not isinstance(data, dict):
            raise IntegrationCatalogError(
                f"Invalid catalog config {config_path}: expected a YAML mapping at the root"
            )
        catalogs_data = data.get("catalogs", [])
        if not isinstance(catalogs_data, list):
            raise IntegrationCatalogError(
                f"Invalid catalog config: 'catalogs' must be a list, "
                f"got {type(catalogs_data).__name__}"
            )
        if not catalogs_data:
            raise IntegrationCatalogError(
                f"Catalog config {config_path} exists but contains no 'catalogs' entries. "
                f"Remove the file to use built-in defaults, or add valid catalog entries."
            )
        entries: List[IntegrationCatalogEntry] = []
        skipped: List[int] = []
        for idx, item in enumerate(catalogs_data):
            if not isinstance(item, dict):
                raise IntegrationCatalogError(
                    f"Invalid catalog entry at index {idx}: "
                    f"expected a mapping, got {type(item).__name__}"
                )
            url = str(item.get("url", "")).strip()
            if not url:
                skipped.append(idx)
                continue
            self._validate_catalog_url(url)
            try:
                priority = int(item.get("priority", idx + 1))
            except (TypeError, ValueError):
                raise IntegrationCatalogError(
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {item.get('priority')!r}"
                )
            raw_install = item.get("install_allowed", False)
            if isinstance(raw_install, str):
                install_allowed = raw_install.strip().lower() in ("true", "yes", "1")
            else:
                install_allowed = bool(raw_install)
            entries.append(
                IntegrationCatalogEntry(
                    url=url,
                    name=str(item.get("name", f"catalog-{idx + 1}")),
                    priority=priority,
                    install_allowed=install_allowed,
                    description=str(item.get("description", "")),
                )
            )
        entries.sort(key=lambda e: e.priority)
        if not entries:
            raise IntegrationCatalogError(
                f"Catalog config {config_path} contains {len(catalogs_data)} "
                f"entries but none have valid URLs (entries at indices {skipped} "
                f"were skipped). Each catalog entry must have a 'url' field."
            )
        return entries