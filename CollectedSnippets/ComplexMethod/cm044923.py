def _unregister_skills(self, skill_names: List[str], preset_dir: Path) -> None:
        """Restore original SKILL.md files after a preset is removed.

        For each skill that was overridden by the preset, attempts to
        regenerate the skill from the core command template.  If no core
        template exists, the skill directory is removed.

        Args:
            skill_names: List of skill names written by the preset.
            preset_dir: The preset's installed directory (may already be deleted).
        """
        if not skill_names:
            return

        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return

        from . import SKILL_DESCRIPTIONS, load_init_options
        from .agents import CommandRegistrar
        from .integrations import get_integration

        # Locate core command templates from the project's installed templates
        core_templates_dir = self.project_root / ".specify" / "templates" / "commands"
        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = init_opts.get("ai")
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai) if isinstance(selected_ai, str) else None
        extension_restore_index = self._build_extension_skill_restore_index()

        for skill_name in skill_names:
            # Derive command name from skill name (speckit-specify -> specify)
            short_name = skill_name
            if short_name.startswith("speckit-"):
                short_name = short_name[len("speckit-"):]
            elif short_name.startswith("speckit."):
                short_name = short_name[len("speckit."):]

            skill_subdir = skills_dir / skill_name
            skill_file = skill_subdir / "SKILL.md"
            if not skill_subdir.is_dir():
                continue
            if not skill_file.is_file():
                # Only manage directories that contain the expected skill entrypoint.
                continue

            # Try to find the core command template
            core_file = core_templates_dir / f"{short_name}.md" if core_templates_dir.exists() else None
            if core_file and not core_file.exists():
                core_file = None

            if core_file:
                # Restore from core template
                content = core_file.read_text(encoding="utf-8")
                frontmatter, body = registrar.parse_frontmatter(content)
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root
                    )

                original_desc = frontmatter.get("description", "")
                enhanced_desc = SKILL_DESCRIPTIONS.get(
                    short_name,
                    original_desc or f"Spec-kit workflow command: {short_name}",
                )

                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai if isinstance(selected_ai, str) else "",
                    skill_name,
                    enhanced_desc,
                    f"templates/commands/{short_name}.md",
                )
                frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
                skill_title = self._skill_title_from_command(short_name)
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
                skill_file.write_text(skill_content, encoding="utf-8")
                continue

            extension_restore = extension_restore_index.get(skill_name)
            if extension_restore:
                content = extension_restore["source_file"].read_text(encoding="utf-8")
                frontmatter, body = registrar.parse_frontmatter(content)
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root
                    )

                command_name = extension_restore["command_name"]
                title_name = self._skill_title_from_command(command_name)

                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai if isinstance(selected_ai, str) else "",
                    skill_name,
                    frontmatter.get("description", f"Extension command: {command_name}"),
                    extension_restore["source"],
                )
                frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# {title_name} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )
                skill_file.write_text(skill_content, encoding="utf-8")
            else:
                # No core or extension template — remove the skill entirely
                shutil.rmtree(skill_subdir)