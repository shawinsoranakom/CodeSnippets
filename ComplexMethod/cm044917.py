def _validate(self):
        """Validate manifest structure and required fields."""
        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise PresetValidationError(f"Missing required field: {field}")

        # Validate schema version
        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise PresetValidationError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        # Validate preset metadata
        pack = self.data["preset"]
        for field in ["id", "name", "version", "description"]:
            if field not in pack:
                raise PresetValidationError(f"Missing preset.{field}")

        # Validate pack ID format
        if not re.match(r'^[a-z0-9-]+$', pack["id"]):
            raise PresetValidationError(
                f"Invalid preset ID '{pack['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(pack["version"])
        except pkg_version.InvalidVersion:
            raise PresetValidationError(f"Invalid version: {pack['version']}")

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise PresetValidationError("Missing requires.speckit_version")

        # Validate provides section
        provides = self.data["provides"]
        if "templates" not in provides or not provides["templates"]:
            raise PresetValidationError(
                "Preset must provide at least one template"
            )

        # Validate templates
        for tmpl in provides["templates"]:
            if "type" not in tmpl or "name" not in tmpl or "file" not in tmpl:
                raise PresetValidationError(
                    "Template missing 'type', 'name', or 'file'"
                )

            if tmpl["type"] not in VALID_PRESET_TEMPLATE_TYPES:
                raise PresetValidationError(
                    f"Invalid template type '{tmpl['type']}': "
                    f"must be one of {sorted(VALID_PRESET_TEMPLATE_TYPES)}"
                )

            # Validate file path safety: must be relative, no parent traversal
            file_path = tmpl["file"]
            normalized = os.path.normpath(file_path)
            if os.path.isabs(normalized) or normalized.startswith(".."):
                raise PresetValidationError(
                    f"Invalid template file path '{file_path}': "
                    "must be a relative path within the preset directory"
                )

            # Validate template name format
            if tmpl["type"] == "command":
                # Commands use dot notation (e.g. speckit.specify)
                if not re.match(r'^[a-z0-9.-]+$', tmpl["name"]):
                    raise PresetValidationError(
                        f"Invalid command name '{tmpl['name']}': "
                        "must be lowercase alphanumeric with hyphens and dots only"
                    )
            else:
                if not re.match(r'^[a-z0-9-]+$', tmpl["name"]):
                    raise PresetValidationError(
                        f"Invalid template name '{tmpl['name']}': "
                        "must be lowercase alphanumeric with hyphens only"
                    )