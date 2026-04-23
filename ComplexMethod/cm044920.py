def _replay_skill_override(
        self,
        cmd_name: str,
        composed_content: str,
        outermost_pack_id: str,
    ) -> None:
        """Rewrite any active SKILL.md override for a replayed wrap command."""
        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return

        from . import SKILL_DESCRIPTIONS, load_init_options
        from .agents import CommandRegistrar
        from .integrations import get_integration

        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = init_opts.get("ai")
        if not isinstance(selected_ai, str):
            return

        registrar = CommandRegistrar()
        integration = get_integration(selected_ai)
        agent_config = registrar.AGENT_CONFIGS.get(selected_ai, {})
        create_missing_skills = bool(init_opts.get("ai_skills")) and agent_config.get("extension") != "/SKILL.md"

        skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
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
            return

        raw_short_name = cmd_name
        if raw_short_name.startswith("speckit."):
            raw_short_name = raw_short_name[len("speckit."):]
        short_name = raw_short_name.replace(".", "-")
        skill_title = self._skill_title_from_command(cmd_name)

        frontmatter, body = registrar.parse_frontmatter(composed_content)
        original_desc = frontmatter.get("description", "")
        enhanced_desc = SKILL_DESCRIPTIONS.get(
            short_name,
            original_desc or f"Spec-kit workflow command: {short_name}",
        )
        body = registrar.resolve_skill_placeholders(
            selected_ai, dict(frontmatter), body, self.project_root
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
                f"preset:{outermost_pack_id}",
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
                skill_content = integration.post_process_skill_content(skill_content)
            (skill_subdir / "SKILL.md").write_text(skill_content, encoding="utf-8")