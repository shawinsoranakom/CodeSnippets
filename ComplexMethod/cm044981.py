def _collect_manifest_command_names(manifest: ExtensionManifest) -> Dict[str, str]:
        """Collect command and alias names declared by a manifest.

        Performs install-time validation for extension-specific constraints:
        - primary commands must use the canonical `speckit.{extension}.{command}` shape
        - primary commands must use this extension's namespace
        - command namespaces must not shadow core commands
        - duplicate command/alias names inside one manifest are rejected
        - aliases are validated for type and uniqueness only (no pattern enforcement)

        Args:
            manifest: Parsed extension manifest

        Returns:
            Mapping of declared command/alias name -> kind ("command"/"alias")

        Raises:
            ValidationError: If any declared name is invalid
        """
        if manifest.id in CORE_COMMAND_NAMES:
            raise ValidationError(
                f"Extension ID '{manifest.id}' conflicts with core command namespace '{manifest.id}'"
            )

        declared_names: Dict[str, str] = {}

        for cmd in manifest.commands:
            primary_name = cmd["name"]
            aliases = cmd.get("aliases", [])

            if aliases is None:
                aliases = []
            if not isinstance(aliases, list):
                raise ValidationError(
                    f"Aliases for command '{primary_name}' must be a list"
                )

            for kind, name in [("command", primary_name)] + [
                ("alias", alias) for alias in aliases
            ]:
                if not isinstance(name, str):
                    raise ValidationError(
                        f"{kind.capitalize()} for command '{primary_name}' must be a string"
                    )

                # Enforce canonical pattern only for primary command names;
                # aliases are free-form to preserve community extension compat.
                if kind == "command":
                    match = EXTENSION_COMMAND_NAME_PATTERN.match(name)
                    if match is None:
                        raise ValidationError(
                            f"Invalid {kind} '{name}': "
                            "must follow pattern 'speckit.{extension}.{command}'"
                        )

                    namespace = match.group(1)
                    if namespace != manifest.id:
                        raise ValidationError(
                            f"{kind.capitalize()} '{name}' must use extension namespace '{manifest.id}'"
                        )

                    if namespace in CORE_COMMAND_NAMES:
                        raise ValidationError(
                            f"{kind.capitalize()} '{name}' conflicts with core command namespace '{namespace}'"
                        )

                if name in declared_names:
                    raise ValidationError(
                        f"Duplicate command or alias '{name}' in extension manifest"
                    )

                declared_names[name] = kind

        return declared_names