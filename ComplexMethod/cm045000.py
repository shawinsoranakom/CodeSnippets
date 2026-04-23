def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "{{args}}")
            if self.registrar_config
            else "{{args}}"
        )
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            fm = self._extract_frontmatter(raw)
            description = fm.get("description", "")
            if not isinstance(description, str):
                description = str(description) if description is not None else ""
            title = fm.get("title", "") or fm.get("name", "")
            if not isinstance(title, str):
                title = str(title) if title is not None else ""
            if not title:
                title = self._human_title(src_file.stem)

            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                context_file=self.context_file or "",
            )
            _, body = self._split_frontmatter(processed)
            yaml_content = self._render_yaml(
                title, description, body, f"templates/commands/{src_file.name}"
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                yaml_content, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)

        # Upsert managed context section into the agent context file
        self.upsert_context_section(project_root)

        return created