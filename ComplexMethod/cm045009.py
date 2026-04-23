def _validate(self) -> None:
        if not isinstance(self.data, dict):
            raise IntegrationDescriptorError(
                f"Descriptor root must be a YAML mapping, got {type(self.data).__name__}"
            )
        for field in self.REQUIRED_TOP_LEVEL:
            if field not in self.data:
                raise IntegrationDescriptorError(
                    f"Missing required field: {field}"
                )

        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise IntegrationDescriptorError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        integ = self.data["integration"]
        if not isinstance(integ, dict):
            raise IntegrationDescriptorError(
                "'integration' must be a mapping"
            )
        for field in ("id", "name", "version", "description"):
            if field not in integ:
                raise IntegrationDescriptorError(
                    f"Missing integration.{field}"
                )
            if not isinstance(integ[field], str):
                raise IntegrationDescriptorError(
                    f"integration.{field} must be a string, got {type(integ[field]).__name__}"
                )

        if not re.match(r"^[a-z0-9-]+$", integ["id"]):
            raise IntegrationDescriptorError(
                f"Invalid integration ID '{integ['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        try:
            pkg_version.Version(integ["version"])
        except (pkg_version.InvalidVersion, TypeError):
            raise IntegrationDescriptorError(
                f"Invalid version '{integ['version']}'"
            )

        requires = self.data["requires"]
        if not isinstance(requires, dict):
            raise IntegrationDescriptorError(
                "'requires' must be a mapping"
            )
        if "speckit_version" not in requires:
            raise IntegrationDescriptorError(
                "Missing requires.speckit_version"
            )
        if not isinstance(requires["speckit_version"], str) or not requires["speckit_version"].strip():
            raise IntegrationDescriptorError(
                "requires.speckit_version must be a non-empty string"
            )
        tools = requires.get("tools")
        if tools is not None:
            if not isinstance(tools, list):
                raise IntegrationDescriptorError(
                    "requires.tools must be a list"
                )
            for tool in tools:
                if not isinstance(tool, dict):
                    raise IntegrationDescriptorError(
                        "Each requires.tools entry must be a mapping"
                    )
                tool_name = tool.get("name")
                if not isinstance(tool_name, str) or not tool_name.strip():
                    raise IntegrationDescriptorError(
                        "requires.tools entry 'name' must be a non-empty string"
                    )

        provides = self.data["provides"]
        if not isinstance(provides, dict):
            raise IntegrationDescriptorError(
                "'provides' must be a mapping"
            )
        commands = provides.get("commands", [])
        scripts = provides.get("scripts", [])
        if "commands" in provides and not isinstance(commands, list):
            raise IntegrationDescriptorError(
                "Invalid provides.commands: expected a list"
            )
        if "scripts" in provides and not isinstance(scripts, list):
            raise IntegrationDescriptorError(
                "Invalid provides.scripts: expected a list"
            )
        if not commands and not scripts:
            raise IntegrationDescriptorError(
                "Integration must provide at least one command or script"
            )
        for cmd in commands:
            if not isinstance(cmd, dict):
                raise IntegrationDescriptorError(
                    "Each command entry must be a mapping"
                )
            if "name" not in cmd or "file" not in cmd:
                raise IntegrationDescriptorError(
                    "Command entry missing 'name' or 'file'"
                )
            cmd_name = cmd["name"]
            cmd_file = cmd["file"]
            if not isinstance(cmd_name, str) or not cmd_name.strip():
                raise IntegrationDescriptorError(
                    "Command entry 'name' must be a non-empty string"
                )
            if not isinstance(cmd_file, str) or not cmd_file.strip():
                raise IntegrationDescriptorError(
                    "Command entry 'file' must be a non-empty string"
                )
            if os.path.isabs(cmd_file) or ".." in Path(cmd_file).parts or Path(cmd_file).drive or Path(cmd_file).anchor:
                raise IntegrationDescriptorError(
                    f"Command entry 'file' must be a relative path without '..': {cmd_file}"
                )
        for script_entry in scripts:
            if not isinstance(script_entry, str) or not script_entry.strip():
                raise IntegrationDescriptorError(
                    "Script entry must be a non-empty string"
                )
            if os.path.isabs(script_entry) or ".." in Path(script_entry).parts or Path(script_entry).drive or Path(script_entry).anchor:
                raise IntegrationDescriptorError(
                    f"Script entry must be a relative path without '..': {script_entry}"
                )