def _register_extension_skills(
        self,
        manifest: ExtensionManifest,
        extension_dir: Path,
    ) -> List[str]:
        """Generate SKILL.md files for extension commands as agent skills.

        For every command in the extension manifest, creates a SKILL.md
        file in the agent's skills directory following the agentskills.io
        specification.  This is only done when ``--ai-skills`` was used
        during project initialisation.

        Args:
            manifest: Extension manifest.
            extension_dir: Installed extension directory.

        Returns:
            List of skill names that were created (for registry storage).
        """
        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return []

        from . import load_init_options
        from .agents import CommandRegistrar
        from .integrations import get_integration
        import yaml

        written: List[str] = []
        opts = load_init_options(self.project_root)
        if not isinstance(opts, dict):
            opts = {}
        selected_ai = opts.get("ai")
        if not isinstance(selected_ai, str) or not selected_ai:
            return []
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai)

        for cmd_info in manifest.commands:
            cmd_name = cmd_info["name"]
            cmd_file_rel = cmd_info["file"]

            # Guard against path traversal: reject absolute paths and ensure
            # the resolved file stays within the extension directory.
            cmd_path = Path(cmd_file_rel)
            if cmd_path.is_absolute():
                continue
            try:
                ext_root = extension_dir.resolve()
                source_file = (ext_root / cmd_path).resolve()
                source_file.relative_to(ext_root)  # raises ValueError if outside
            except (OSError, ValueError):
                continue

            if not source_file.is_file():
                continue

            # Derive skill name from command name using the same hyphenated
            # convention as hook rendering and preset skill registration.
            short_name_raw = cmd_name
            if short_name_raw.startswith("speckit."):
                short_name_raw = short_name_raw[len("speckit."):]
            skill_name = f"speckit-{short_name_raw.replace('.', '-')}"

            # Check if skill already exists before creating the directory
            skill_subdir = skills_dir / skill_name
            skill_file = skill_subdir / "SKILL.md"
            if skill_file.exists():
                # Do not overwrite user-customized skills
                continue

            # Create skill directory; track whether we created it so we can clean
            # up safely if reading the source file subsequently fails.
            created_now = not skill_subdir.exists()
            skill_subdir.mkdir(parents=True, exist_ok=True)

            # Parse the command file — guard against IsADirectoryError / decode errors
            try:
                content = source_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                if created_now:
                    try:
                        skill_subdir.rmdir()  # undo the mkdir; dir is empty at this point
                    except OSError:
                        pass  # best-effort cleanup
                continue
            frontmatter, body = registrar.parse_frontmatter(content)
            frontmatter = registrar._adjust_script_paths(frontmatter)
            body = registrar.resolve_skill_placeholders(
                selected_ai, frontmatter, body, self.project_root
            )

            original_desc = frontmatter.get("description", "")
            description = original_desc or f"Extension command: {cmd_name}"

            frontmatter_data = registrar.build_skill_frontmatter(
                selected_ai,
                skill_name,
                description,
                f"extension:{manifest.id}",
            )
            frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()

            # Derive a human-friendly title from the command name
            short_name = cmd_name
            if short_name.startswith("speckit."):
                short_name = short_name[len("speckit."):]
            title_name = short_name.replace(".", " ").replace("-", " ").title()

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
            written.append(skill_name)

        return written