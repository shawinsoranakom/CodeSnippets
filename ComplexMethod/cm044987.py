def _load_catalog_config(self, config_path: Path) -> Optional[List[CatalogEntry]]:
        """Load catalog stack configuration from a YAML file.

        Args:
            config_path: Path to extension-catalogs.yml

        Returns:
            Ordered list of CatalogEntry objects, or None if file doesn't exist.

        Raises:
            ValidationError: If any catalog entry has an invalid URL,
                the file cannot be parsed, a priority value is invalid,
                or the file exists but contains no valid catalog entries
                (fail-closed for security).
        """
        if not config_path.exists():
            return None
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError, UnicodeError) as e:
            raise ValidationError(
                f"Failed to read catalog config {config_path}: {e}"
            )
        catalogs_data = data.get("catalogs", [])
        if not catalogs_data:
            # File exists but has no catalogs key or empty list - fail closed
            raise ValidationError(
                f"Catalog config {config_path} exists but contains no 'catalogs' entries. "
                f"Remove the file to use built-in defaults, or add valid catalog entries."
            )
        if not isinstance(catalogs_data, list):
            raise ValidationError(
                f"Invalid catalog config: 'catalogs' must be a list, got {type(catalogs_data).__name__}"
            )
        entries: List[CatalogEntry] = []
        skipped_entries: List[int] = []
        for idx, item in enumerate(catalogs_data):
            if not isinstance(item, dict):
                raise ValidationError(
                    f"Invalid catalog entry at index {idx}: expected a mapping, got {type(item).__name__}"
                )
            url = str(item.get("url", "")).strip()
            if not url:
                skipped_entries.append(idx)
                continue
            self._validate_catalog_url(url)
            try:
                priority = int(item.get("priority", idx + 1))
            except (TypeError, ValueError):
                raise ValidationError(
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {item.get('priority')!r}"
                )
            raw_install = item.get("install_allowed", False)
            if isinstance(raw_install, str):
                install_allowed = raw_install.strip().lower() in ("true", "yes", "1")
            else:
                install_allowed = bool(raw_install)
            entries.append(CatalogEntry(
                url=url,
                name=str(item.get("name", f"catalog-{idx + 1}")),
                priority=priority,
                install_allowed=install_allowed,
                description=str(item.get("description", "")),
            ))
        entries.sort(key=lambda e: e.priority)
        if not entries:
            # All entries were invalid (missing URLs) - fail closed for security
            raise ValidationError(
                f"Catalog config {config_path} contains {len(catalogs_data)} entries but none have valid URLs "
                f"(entries at indices {skipped_entries} were skipped). "
                f"Each catalog entry must have a 'url' field."
            )
        return entries