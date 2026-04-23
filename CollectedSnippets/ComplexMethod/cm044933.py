def resolve(
        self,
        template_name: str,
        template_type: str = "template",
        skip_presets: bool = False,
    ) -> Optional[Path]:
        """Resolve a template name to its file path.

        Walks the priority stack and returns the first match.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")
            skip_presets: When True, skip tier 2 (installed presets). Use
                resolve_core() as the preferred caller-facing API for this.

        Returns:
            Path to the resolved template file, or None if not found
        """
        # Determine subdirectory based on template type
        if template_type == "template":
            subdirs = ["templates", ""]
        elif template_type == "command":
            subdirs = ["commands"]
        elif template_type == "script":
            subdirs = ["scripts"]
        else:
            subdirs = [""]

        # Determine file extension based on template type
        ext = ".md"
        if template_type == "script":
            ext = ".sh"  # scripts use .sh; callers can also check .ps1

        # Priority 1: Project-local overrides
        if template_type == "script":
            override = self.overrides_dir / "scripts" / f"{template_name}{ext}"
        else:
            override = self.overrides_dir / f"{template_name}{ext}"
        if override.exists():
            return override

        # Priority 2: Installed presets (sorted by priority — lower number wins)
        if not skip_presets and self.presets_dir.exists():
            registry = PresetRegistry(self.presets_dir)
            for pack_id, _metadata in registry.list_by_priority():
                pack_dir = self.presets_dir / pack_id
                for subdir in subdirs:
                    if subdir:
                        candidate = pack_dir / subdir / f"{template_name}{ext}"
                    else:
                        candidate = pack_dir / f"{template_name}{ext}"
                    if candidate.exists():
                        return candidate

        # Priority 3: Extension-provided templates (sorted by priority — lower number wins)
        for _priority, ext_id, _metadata in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            if not ext_dir.is_dir():
                continue
            for subdir in subdirs:
                if subdir:
                    candidate = ext_dir / subdir / f"{template_name}{ext}"
                else:
                    candidate = ext_dir / f"{template_name}{ext}"
                if candidate.exists():
                    return candidate

        # Priority 4: Core templates
        if template_type == "template":
            core = self.templates_dir / f"{template_name}.md"
            if core.exists():
                return core
        elif template_type == "command":
            core = self.templates_dir / "commands" / f"{template_name}.md"
            if core.exists():
                return core
        elif template_type == "script":
            core = self.templates_dir / "scripts" / f"{template_name}{ext}"
            if core.exists():
                return core

        # Priority 5: Bundled core_pack (wheel install) or repo-root templates
        # (source-checkout / editable install).  This is the canonical home for
        # speckit's built-in command/template files and must always be checked
        # so that strategy:wrap presets can locate {CORE_TEMPLATE}.
        from specify_cli import _locate_core_pack  # local import to avoid cycles
        _core_pack = _locate_core_pack()
        if _core_pack is not None:
            # Wheel install path
            if template_type == "template":
                candidate = _core_pack / "templates" / f"{template_name}.md"
            elif template_type == "command":
                candidate = _core_pack / "commands" / f"{template_name}.md"
            elif template_type == "script":
                candidate = _core_pack / "scripts" / f"{template_name}{ext}"
            else:
                candidate = _core_pack / f"{template_name}.md"
            if candidate.exists():
                return candidate
        else:
            # Source-checkout / editable install: templates live at repo root
            repo_root = Path(__file__).parent.parent.parent
            if template_type == "template":
                candidate = repo_root / "templates" / f"{template_name}.md"
            elif template_type == "command":
                candidate = repo_root / "templates" / "commands" / f"{template_name}.md"
            elif template_type == "script":
                candidate = repo_root / "scripts" / f"{template_name}{ext}"
            else:
                candidate = repo_root / f"{template_name}.md"
            if candidate.exists():
                return candidate

        return None