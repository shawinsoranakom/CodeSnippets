def add_catalog(self, url: str, name: str | None = None) -> None:
        """Add a catalog source to the project-level config."""
        self._validate_catalog_url(url)
        config_path = self.project_root / ".specify" / "workflow-catalogs.yml"

        data: dict[str, Any] = {"catalogs": []}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise WorkflowValidationError(
                    "Catalog config file is corrupted (expected a mapping)."
                )
            data = raw

        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list):
            raise WorkflowValidationError(
                "Catalog config 'catalogs' must be a list."
            )
        # Check for duplicate URL (guard against non-dict entries)
        for cat in catalogs:
            if isinstance(cat, dict) and cat.get("url") == url:
                raise WorkflowValidationError(
                    f"Catalog URL already configured: {url}"
                )

        # Derive priority from the highest existing priority + 1
        max_priority = max(
            (cat.get("priority", 0) for cat in catalogs if isinstance(cat, dict)),
            default=0,
        )
        catalogs.append(
            {
                "name": name or f"catalog-{len(catalogs) + 1}",
                "url": url,
                "priority": max_priority + 1,
                "install_allowed": True,
                "description": "",
            }
        )
        data["catalogs"] = catalogs

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)