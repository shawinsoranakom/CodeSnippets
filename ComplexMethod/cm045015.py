def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install copilot commands, companion prompts, and VS Code settings.

        Uses base class primitives to: read templates, process them
        (replace placeholders, strip script blocks, rewrite paths),
        write as ``.agent.md``, then add companion prompts and VS Code settings.
        """
        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        templates = self.list_command_templates()
        if not templates:
            return []

        dest = self.commands_dest(project_root)
        dest_resolved = dest.resolve()
        try:
            dest_resolved.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest_resolved} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        script_type = opts.get("script_type", "sh")
        arg_placeholder = self.registrar_config.get("args", "$ARGUMENTS")

        # 1. Process and write command files as .agent.md
        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                context_file=self.context_file or "",
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)

        # 2. Generate companion .prompt.md files from the templates we just wrote
        prompts_dir = project_root / ".github" / "prompts"
        for src_file in templates:
            cmd_name = f"speckit.{src_file.stem}"
            prompt_content = f"---\nagent: {cmd_name}\n---\n"
            prompt_file = self.write_file_and_record(
                prompt_content,
                prompts_dir / f"{cmd_name}.prompt.md",
                project_root,
                manifest,
            )
            created.append(prompt_file)

        # Write .vscode/settings.json
        settings_src = self._vscode_settings_path()
        if settings_src and settings_src.is_file():
            dst_settings = project_root / ".vscode" / "settings.json"
            dst_settings.parent.mkdir(parents=True, exist_ok=True)
            if dst_settings.exists():
                # Merge into existing — don't track since we can't safely
                # remove the user's settings file on uninstall.
                self._merge_vscode_settings(settings_src, dst_settings)
            else:
                shutil.copy2(settings_src, dst_settings)
                self.record_file_in_manifest(dst_settings, project_root, manifest)
                created.append(dst_settings)

        # 4. Upsert managed context section into the agent context file
        self.upsert_context_section(project_root)

        return created