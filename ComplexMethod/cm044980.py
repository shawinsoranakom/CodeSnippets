def _validate(self):
        """Validate manifest structure and required fields."""
        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate schema version
        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise ValidationError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        # Validate extension metadata
        ext = self.data["extension"]
        for field in ["id", "name", "version", "description"]:
            if field not in ext:
                raise ValidationError(f"Missing extension.{field}")

        # Validate extension ID format
        if not re.match(r'^[a-z0-9-]+$', ext["id"]):
            raise ValidationError(
                f"Invalid extension ID '{ext['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(ext["version"])
        except pkg_version.InvalidVersion:
            raise ValidationError(f"Invalid version: {ext['version']}")

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise ValidationError("Missing requires.speckit_version")

        # Validate provides section
        provides = self.data["provides"]
        commands = provides.get("commands", [])
        hooks = self.data.get("hooks")

        if "commands" in provides and not isinstance(commands, list):
            raise ValidationError(
                "Invalid provides.commands: expected a list"
            )
        if "hooks" in self.data and not isinstance(hooks, dict):
            raise ValidationError(
                "Invalid hooks: expected a mapping"
            )

        has_commands = bool(commands)
        has_hooks = bool(hooks)

        if not has_commands and not has_hooks:
            raise ValidationError(
                "Extension must provide at least one command or hook"
            )

        # Validate hook values (if present)
        if hooks:
            for hook_name, hook_config in hooks.items():
                if not isinstance(hook_config, dict):
                    raise ValidationError(
                        f"Invalid hook '{hook_name}': expected a mapping"
                    )
                if not hook_config.get("command"):
                    raise ValidationError(
                        f"Hook '{hook_name}' missing required 'command' field"
                    )

        # Validate commands; track renames so hook references can be rewritten.
        rename_map: Dict[str, str] = {}
        for cmd in commands:
            if not isinstance(cmd, dict):
                raise ValidationError(
                    "Each command entry in 'provides.commands' must be a mapping"
                )
            if "name" not in cmd or "file" not in cmd:
                raise ValidationError("Command missing 'name' or 'file'")

            # Validate command name format
            if not EXTENSION_COMMAND_NAME_PATTERN.match(cmd["name"]):
                corrected = self._try_correct_command_name(cmd["name"], ext["id"])
                if corrected:
                    self.warnings.append(
                        f"Command name '{cmd['name']}' does not follow the required pattern "
                        f"'speckit.{{extension}}.{{command}}'. Registering as '{corrected}'. "
                        f"The extension author should update the manifest to use this name."
                    )
                    rename_map[cmd["name"]] = corrected
                    cmd["name"] = corrected
                else:
                    raise ValidationError(
                        f"Invalid command name '{cmd['name']}': "
                        "must follow pattern 'speckit.{extension}.{command}'"
                    )

            # Validate alias types; no pattern enforcement on aliases — they are
            # intentionally free-form to preserve community extension compatibility
            # (e.g. 'speckit.verify' short aliases used by existing extensions).
            aliases = cmd.get("aliases")
            if aliases is None:
                cmd["aliases"] = []
                aliases = []
            if not isinstance(aliases, list):
                raise ValidationError(
                    f"Aliases for command '{cmd['name']}' must be a list"
                )
            for alias in aliases:
                if not isinstance(alias, str):
                    raise ValidationError(
                        f"Aliases for command '{cmd['name']}' must be strings"
                    )

        # Rewrite any hook command references that pointed at a renamed command or
        # an alias-form ref (ext.cmd → speckit.ext.cmd).  Always emit a warning when
        # the reference is changed so extension authors know to update the manifest.
        for hook_name, hook_data in self.data.get("hooks", {}).items():
            if not isinstance(hook_data, dict):
                raise ValidationError(
                    f"Hook '{hook_name}' must be a mapping, got {type(hook_data).__name__}"
                )
            command_ref = hook_data.get("command")
            if not isinstance(command_ref, str):
                continue
            # Step 1: apply any rename from the auto-correction pass.
            after_rename = rename_map.get(command_ref, command_ref)
            # Step 2: lift alias-form '{ext_id}.cmd' to canonical 'speckit.{ext_id}.cmd'.
            parts = after_rename.split(".")
            if len(parts) == 2 and parts[0] == ext["id"]:
                final_ref = f"speckit.{ext['id']}.{parts[1]}"
            else:
                final_ref = after_rename
            if final_ref != command_ref:
                hook_data["command"] = final_ref
                self.warnings.append(
                    f"Hook '{hook_name}' referenced command '{command_ref}'; "
                    f"updated to canonical form '{final_ref}'. "
                    f"The extension author should update the manifest."
                )