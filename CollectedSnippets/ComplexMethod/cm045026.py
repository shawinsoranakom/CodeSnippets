def _load_catalog_config(
        self, config_path: Path
    ) -> list[WorkflowCatalogEntry] | None:
        """Load catalog stack configuration from a YAML file."""
        if not config_path.exists():
            return None
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError, UnicodeError) as exc:
            raise WorkflowValidationError(
                f"Failed to read catalog config {config_path}: {exc}"
            )
        catalogs_data = data.get("catalogs", [])
        if not catalogs_data:
            # Empty catalogs list (e.g. after removing last entry)
            # is valid — fall back to built-in defaults.
            return None
        if not isinstance(catalogs_data, list):
            raise WorkflowValidationError(
                f"Invalid catalog config: 'catalogs' must be a list, "
                f"got {type(catalogs_data).__name__}"
            )

        entries: list[WorkflowCatalogEntry] = []
        for idx, item in enumerate(catalogs_data):
            if not isinstance(item, dict):
                raise WorkflowValidationError(
                    f"Invalid catalog entry at index {idx}: "
                    f"expected a mapping, got {type(item).__name__}"
                )
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            self._validate_catalog_url(url)
            try:
                priority = int(item.get("priority", idx + 1))
            except (TypeError, ValueError):
                raise WorkflowValidationError(
                    f"Invalid priority for catalog "
                    f"'{item.get('name', idx + 1)}': "
                    f"expected integer, got {item.get('priority')!r}"
                )
            raw_install = item.get("install_allowed", False)
            if isinstance(raw_install, str):
                install_allowed = raw_install.strip().lower() in (
                    "true",
                    "yes",
                    "1",
                )
            else:
                install_allowed = bool(raw_install)
            entries.append(
                WorkflowCatalogEntry(
                    url=url,
                    name=str(item.get("name", f"catalog-{idx + 1}")),
                    priority=priority,
                    install_allowed=install_allowed,
                    description=str(item.get("description", "")),
                )
            )
        entries.sort(key=lambda e: e.priority)
        if not entries:
            raise WorkflowValidationError(
                f"Catalog config {config_path} contains {len(catalogs_data)} "
                f"entries but none have valid URLs."
            )
        return entries