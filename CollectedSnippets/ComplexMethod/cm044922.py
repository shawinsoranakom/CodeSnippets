def _register_skills(
        self,
        manifest: "PresetManifest",
        preset_dir: Path,
    ) -> List[str]:
        """Generate SKILL.md files for preset command overrides.

        For every command template in the preset, checks whether a
        corresponding skill already exists in any detected skills
        directory.  If so, the skill is overwritten with content derived
        from the preset's command file.  This ensures that presets that
        override commands also propagate to the agentskills.io skill
        layer when ``--ai-skills`` was used during project initialisation.

        Args:
            manifest: Preset manifest.
            preset_dir: Installed preset directory.

        Returns:
            List of skill names that were written (for registry storage).
        """
        command_templates = [
            t for t in manifest.templates if t.get("type") == "command"
        ]
        if not command_templates:
            return []

        # Filter out extension command overrides if the extension isn't installed,
        # matching the same logic used by _register_commands().
        extensions_dir = self.project_root / ".specify" / "extensions"
        filtered = []
        for cmd in command_templates:
            parts = cmd["name"].split(".")
            if len(parts) >= 3 and parts[0] == "speckit":
                ext_id = parts[1]
                if not (extensions_dir / ext_id).is_dir():
                    continue
            filtered.append(cmd)

        if not filtered:
            return []

        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return []

        from . import SKILL_DESCRIPTIONS, load_init_options
        from .agents import CommandRegistrar
        from .integrations import get_integration

        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = init_opts.get("ai")
        if not isinstance(selected_ai, str):
            return []
        ai_skills_enabled = bool(init_opts.get("ai_skills"))
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai)
        agent_config = registrar.AGENT_CONFIGS.get(selected_ai, {})
        # Native skill agents (e.g. codex/kimi/agy/trae) materialize brand-new
        # preset skills in _register_commands() because their detected agent
        # directory is already the skills directory. This flag is only for
        # command-backed agents that also mirror commands into skills.
        create_missing_skills = ai_skills_enabled and agent_config.get("extension") != "/SKILL.md"

        written: List[str] = []

        for cmd_tmpl in filtered:
            cmd_name = cmd_tmpl["name"]
            cmd_file_rel = cmd_tmpl["file"]
            source_file = preset_dir / cmd_file_rel
            if not source_file.exists():
                continue

            # Derive the short command name (e.g. "specify" from "speckit.specify")
            raw_short_name = cmd_name
            if raw_short_name.startswith("speckit."):
                raw_short_name = raw_short_name[len("speckit."):]
            short_name = raw_short_name.replace(".", "-")
            skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
            skill_title = self._skill_title_from_command(cmd_name)

            # Only overwrite skills that already exist under skills_dir,
            # including Kimi native skills when ai_skills is false.
            # If both modern and legacy directories exist, update both.
            target_skill_names: List[str] = []
            if (skills_dir / skill_name).is_dir():
                target_skill_names.append(skill_name)
            if legacy_skill_name != skill_name and (skills_dir / legacy_skill_name).is_dir():
                target_skill_names.append(legacy_skill_name)
            if not target_skill_names and create_missing_skills:
                missing_skill_dir = skills_dir / skill_name
                if not missing_skill_dir.exists():
                    target_skill_names.append(skill_name)
            if not target_skill_names:
                continue

            # Parse the command file
            content = source_file.read_text(encoding="utf-8")
            frontmatter, body = registrar.parse_frontmatter(content)

            if frontmatter.get("strategy") == "wrap":
                body, core_frontmatter = _substitute_core_template(body, cmd_name, self.project_root, registrar)
                frontmatter = dict(frontmatter)
                for key in ("scripts", "agent_scripts"):
                    if key not in frontmatter and key in core_frontmatter:
                        frontmatter[key] = core_frontmatter[key]

            original_desc = frontmatter.get("description", "")
            enhanced_desc = SKILL_DESCRIPTIONS.get(
                short_name,
                original_desc or f"Spec-kit workflow command: {short_name}",
            )
            frontmatter = dict(frontmatter)
            frontmatter["description"] = enhanced_desc
            body = registrar.resolve_skill_placeholders(
                selected_ai, frontmatter, body, self.project_root
            )

            for target_skill_name in target_skill_names:
                skill_subdir = skills_dir / target_skill_name
                if skill_subdir.exists() and not skill_subdir.is_dir():
                    continue
                skill_subdir.mkdir(parents=True, exist_ok=True)
                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai,
                    target_skill_name,
                    enhanced_desc,
                    f"preset:{manifest.id}",
                )
                frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# Speckit {skill_title} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )

                skill_file = skill_subdir / "SKILL.md"
                skill_file.write_text(skill_content, encoding="utf-8")
                written.append(target_skill_name)

        return written