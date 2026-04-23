def _post_validate_validate_argspec(self, attr: NonInheritableFieldAttribute, value: object, templar: _TE) -> str | None:
        """Validate user input is a bool or string, and return the corresponding argument spec name."""

        # Ensure the configuration is valid
        if isinstance(value, str):
            try:
                value = templar.template(value)
            except AnsibleValueOmittedError:
                value = False

        if not isinstance(value, (str, bool)):
            raise AnsibleParserError(f"validate_argspec must be a boolean or string, not {type(value)}", obj=value)

        # Short-circuit if configuration is turned off or inapplicable
        if not value or self._origin is None:
            return None

        # Use the requested argument spec or fall back to the play name
        argspec_name = None
        if isinstance(value, str):
            argspec_name = value
        elif self._ds.get("name"):
            argspec_name = self.name

        metadata_err = argspec_err = ""
        if not argspec_name:
            argspec_err = (
                "A play name is required when validate_argspec is True. "
                "Alternatively, set validate_argspec to the name of an argument spec."
            )
        if self._metadata_path is None:
            metadata_err = "A playbook meta file is required. Considered:\n  - "
            metadata_err += "\n  - ".join([path.as_posix() for path in self._metadata_candidate_paths])

        if metadata_err or argspec_err:
            error = f"{argspec_err + (' ' if argspec_err else '')}{metadata_err}"
            raise AnsibleParserError(error, obj=self._origin)

        metadata = self._loader.load_from_file(self._metadata_path)

        try:
            metadata = metadata['argument_specs']
            metadata = metadata[argspec_name]
            options = metadata['options']
        except (TypeError, KeyError):
            options = None

        if not isinstance(options, dict):
            raise AnsibleParserError(
                f"No argument spec named '{argspec_name}' in {self._metadata_path}. Minimally expected:\n"
                + yaml_dump({"argument_specs": {f"{argspec_name!s}": {"options": {}}}}),
                obj=metadata,
            )

        return argspec_name