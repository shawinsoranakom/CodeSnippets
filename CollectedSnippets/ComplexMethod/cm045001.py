def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install command templates as agent skills.

        Creates ``speckit-<name>/SKILL.md`` for each shared command
        template.  Each SKILL.md has normalised frontmatter containing
        ``name``, ``description``, ``compatibility``, and ``metadata``.
        """
        import yaml

        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        skills_dir = self.skills_dest(project_root).resolve()
        try:
            skills_dir.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Skills destination {skills_dir} escapes "
                f"project root {project_root_resolved}"
            ) from exc

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "$ARGUMENTS")
            if self.registrar_config
            else "$ARGUMENTS"
        )
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")

            # Derive the skill name from the template stem
            command_name = src_file.stem  # e.g. "plan"
            skill_name = f"speckit-{command_name.replace('.', '-')}"

            # Parse frontmatter for description
            frontmatter: dict[str, Any] = {}
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1])
                        if isinstance(fm, dict):
                            frontmatter = fm
                    except yaml.YAMLError:
                        pass

            # Process body through the standard template pipeline
            processed_body = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                context_file=self.context_file or "",
            )
            # Strip the processed frontmatter — we rebuild it for skills.
            # Preserve leading whitespace in the body to match release ZIP
            # output byte-for-byte (the template body starts with \n after
            # the closing ---).
            if processed_body.startswith("---"):
                parts = processed_body.split("---", 2)
                if len(parts) >= 3:
                    processed_body = parts[2]

            # Select description — use the original template description
            # to stay byte-for-byte identical with release ZIP output.
            description = frontmatter.get("description", "")
            if not description:
                description = f"Spec Kit: {command_name} workflow"

            # Build SKILL.md with manually formatted frontmatter to match
            # the release packaging script output exactly (double-quoted
            # values, no yaml.safe_dump quoting differences).
            def _quote(v: str) -> str:
                escaped = v.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'

            skill_content = (
                f"---\n"
                f"name: {_quote(skill_name)}\n"
                f"description: {_quote(description)}\n"
                f"compatibility: {_quote('Requires spec-kit project structure with .specify/ directory')}\n"
                f"metadata:\n"
                f"  author: {_quote('github-spec-kit')}\n"
                f"  source: {_quote('templates/commands/' + src_file.name)}\n"
                f"---\n"
                f"{processed_body}"
            )

            # Write speckit-<name>/SKILL.md
            skill_dir = skills_dir / skill_name
            skill_file = skill_dir / "SKILL.md"
            dst = self.write_file_and_record(
                skill_content, skill_file, project_root, manifest
            )
            created.append(dst)

        # Upsert managed context section into the agent context file
        self.upsert_context_section(project_root)

        return created