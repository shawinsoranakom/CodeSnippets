def register_commands(
        self,
        agent_name: str,
        commands: List[Dict[str, Any]],
        source_id: str,
        source_dir: Path,
        project_root: Path,
        context_note: str = None,
    ) -> List[str]:
        """Register commands for a specific agent.

        Args:
            agent_name: Agent name (claude, gemini, copilot, etc.)
            commands: List of command info dicts with 'name', 'file', and optional 'aliases'
            source_id: Identifier of the source (extension or preset ID)
            source_dir: Directory containing command source files
            project_root: Path to project root
            context_note: Custom context comment for markdown output

        Returns:
            List of registered command names

        Raises:
            ValueError: If agent is not supported
        """
        self._ensure_configs()
        if agent_name not in self.AGENT_CONFIGS:
            raise ValueError(f"Unsupported agent: {agent_name}")

        agent_config = self.AGENT_CONFIGS[agent_name]
        commands_dir = project_root / agent_config["dir"]
        commands_dir.mkdir(parents=True, exist_ok=True)

        registered = []

        for cmd_info in commands:
            cmd_name = cmd_info["name"]
            cmd_file = cmd_info["file"]

            source_file = source_dir / cmd_file
            if not source_file.exists():
                continue

            content = source_file.read_text(encoding="utf-8")
            frontmatter, body = self.parse_frontmatter(content)

            if frontmatter.get("strategy") == "wrap":
                from .presets import _substitute_core_template
                body, core_frontmatter = _substitute_core_template(body, cmd_name, project_root, self)
                frontmatter = dict(frontmatter)
                for key in ("scripts", "agent_scripts"):
                    if key not in frontmatter and key in core_frontmatter:
                        frontmatter[key] = core_frontmatter[key]
                frontmatter.pop("strategy", None)

            frontmatter = self._adjust_script_paths(frontmatter)

            for key in agent_config.get("strip_frontmatter_keys", []):
                frontmatter.pop(key, None)

            if agent_config.get("inject_name") and not frontmatter.get("name"):
                # Use custom name formatter if provided (e.g., Forge's hyphenated format)
                format_name = agent_config.get("format_name")
                frontmatter["name"] = format_name(cmd_name) if format_name else cmd_name

            body = self._convert_argument_placeholder(
                body, "$ARGUMENTS", agent_config["args"]
            )

            output_name = self._compute_output_name(agent_name, cmd_name, agent_config)

            if agent_config["extension"] == "/SKILL.md":
                output = self.render_skill_command(
                    agent_name,
                    output_name,
                    frontmatter,
                    body,
                    source_id,
                    cmd_file,
                    project_root,
                )
            elif agent_config["format"] == "markdown":
                body = self.resolve_skill_placeholders(agent_name, frontmatter, body, project_root)
                body = self._convert_argument_placeholder(body, "$ARGUMENTS", agent_config["args"])
                output = self.render_markdown_command(frontmatter, body, source_id, context_note)
            elif agent_config["format"] == "toml":
                body = self.resolve_skill_placeholders(agent_name, frontmatter, body, project_root)
                body = self._convert_argument_placeholder(body, "$ARGUMENTS", agent_config["args"])
                output = self.render_toml_command(frontmatter, body, source_id)
            elif agent_config["format"] == "yaml":
                output = self.render_yaml_command(
                    frontmatter, body, source_id, cmd_name
                )
            else:
                raise ValueError(f"Unsupported format: {agent_config['format']}")

            dest_file = commands_dir / f"{output_name}{agent_config['extension']}"
            self._ensure_inside(dest_file, commands_dir)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(output, encoding="utf-8")

            if agent_name == "copilot":
                self.write_copilot_prompt(project_root, cmd_name)

            registered.append(cmd_name)

            for alias in cmd_info.get("aliases", []):
                alias_output_name = self._compute_output_name(
                    agent_name, alias, agent_config
                )

                # For agents with inject_name, render with alias-specific frontmatter
                if agent_config.get("inject_name"):
                    alias_frontmatter = deepcopy(frontmatter)
                    # Use custom name formatter if provided (e.g., Forge's hyphenated format)
                    format_name = agent_config.get("format_name")
                    alias_frontmatter["name"] = (
                        format_name(alias) if format_name else alias
                    )

                    if agent_config["extension"] == "/SKILL.md":
                        alias_output = self.render_skill_command(
                            agent_name,
                            alias_output_name,
                            alias_frontmatter,
                            body,
                            source_id,
                            cmd_file,
                            project_root,
                        )
                    elif agent_config["format"] == "markdown":
                        alias_output = self.render_markdown_command(
                            alias_frontmatter, body, source_id, context_note
                        )
                    elif agent_config["format"] == "toml":
                        alias_output = self.render_toml_command(
                            alias_frontmatter, body, source_id
                        )
                    elif agent_config["format"] == "yaml":
                        alias_output = self.render_yaml_command(
                            alias_frontmatter, body, source_id, alias
                        )
                    else:
                        raise ValueError(
                            f"Unsupported format: {agent_config['format']}"
                        )
                else:
                    # For other agents, reuse the primary output
                    alias_output = output
                    if agent_config["extension"] == "/SKILL.md":
                        alias_output = self.render_skill_command(
                            agent_name,
                            alias_output_name,
                            frontmatter,
                            body,
                            source_id,
                            cmd_file,
                            project_root,
                        )

                alias_file = (
                    commands_dir / f"{alias_output_name}{agent_config['extension']}"
                )
                self._ensure_inside(alias_file, commands_dir)
                alias_file.parent.mkdir(parents=True, exist_ok=True)
                alias_file.write_text(alias_output, encoding="utf-8")
                if agent_name == "copilot":
                    self.write_copilot_prompt(project_root, alias)
                registered.append(alias)

        return registered