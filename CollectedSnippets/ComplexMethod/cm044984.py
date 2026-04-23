def _unregister_extension_skills(self, skill_names: List[str], extension_id: str) -> None:
        """Remove SKILL.md directories for extension skills.

        Called during extension removal to clean up skill files that
        were created by ``_register_extension_skills()``.

        If ``_get_skills_dir()`` returns ``None`` (e.g. the user removed
        init-options.json or toggled ai_skills after installation), we
        fall back to scanning all known agent skills directories so that
        orphaned skill directories are still cleaned up.  In that case
        each candidate directory is verified against the SKILL.md
        ``metadata.source`` field before removal to avoid accidentally
        deleting user-created skills with the same name.

        Args:
            skill_names: List of skill names to remove.
            extension_id: Extension ID used to verify ownership during
                fallback candidate scanning.
        """
        if not skill_names:
            return

        skills_dir = self._get_skills_dir()

        if skills_dir:
            # Fast path: we know the exact skills directory
            for skill_name in skill_names:
                # Guard against path traversal from a corrupted registry entry:
                # reject names that are absolute, contain path separators, or
                # resolve to a path outside the skills directory.
                sn_path = Path(skill_name)
                if sn_path.is_absolute() or len(sn_path.parts) != 1:
                    continue
                try:
                    skill_subdir = (skills_dir / skill_name).resolve()
                    skill_subdir.relative_to(skills_dir.resolve())  # raises if outside
                except (OSError, ValueError):
                    continue
                if not skill_subdir.is_dir():
                    continue
                # Safety check: only delete if SKILL.md exists and its
                # metadata.source matches exactly this extension — mirroring
                # the fallback branch — so a corrupted registry entry cannot
                # delete an unrelated user skill.
                skill_md = skill_subdir / "SKILL.md"
                if not skill_md.is_file():
                    continue
                try:
                    import yaml as _yaml
                    raw = skill_md.read_text(encoding="utf-8")
                    source = ""
                    if raw.startswith("---"):
                        parts = raw.split("---", 2)
                        if len(parts) >= 3:
                            fm = _yaml.safe_load(parts[1]) or {}
                            source = (
                                fm.get("metadata", {}).get("source", "")
                                if isinstance(fm, dict)
                                else ""
                            )
                    if source != f"extension:{extension_id}":
                        continue
                except (OSError, UnicodeDecodeError, Exception):
                    continue
                shutil.rmtree(skill_subdir)
        else:
            # Fallback: scan all possible agent skills directories
            from . import AGENT_CONFIG, DEFAULT_SKILLS_DIR

            candidate_dirs: set[Path] = set()
            for cfg in AGENT_CONFIG.values():
                folder = cfg.get("folder", "")
                if folder:
                    candidate_dirs.add(self.project_root / folder.rstrip("/") / "skills")
            candidate_dirs.add(self.project_root / DEFAULT_SKILLS_DIR)

            for skills_candidate in candidate_dirs:
                if not skills_candidate.is_dir():
                    continue
                for skill_name in skill_names:
                    # Same path-traversal guard as the fast path above
                    sn_path = Path(skill_name)
                    if sn_path.is_absolute() or len(sn_path.parts) != 1:
                        continue
                    try:
                        skill_subdir = (skills_candidate / skill_name).resolve()
                        skill_subdir.relative_to(skills_candidate.resolve())  # raises if outside
                    except (OSError, ValueError):
                        continue
                    if not skill_subdir.is_dir():
                        continue
                    # Safety check: only delete if SKILL.md exists and its
                    # metadata.source matches exactly this extension.  If the
                    # file is missing or unreadable we skip to avoid deleting
                    # unrelated user-created directories.
                    skill_md = skill_subdir / "SKILL.md"
                    if not skill_md.is_file():
                        continue
                    try:
                        import yaml as _yaml
                        raw = skill_md.read_text(encoding="utf-8")
                        source = ""
                        if raw.startswith("---"):
                            parts = raw.split("---", 2)
                            if len(parts) >= 3:
                                fm = _yaml.safe_load(parts[1]) or {}
                                source = (
                                    fm.get("metadata", {}).get("source", "")
                                    if isinstance(fm, dict)
                                    else ""
                                )
                        # Only remove skills explicitly created by this extension
                        if source != f"extension:{extension_id}":
                            continue
                    except (OSError, UnicodeDecodeError, Exception):
                        # If we can't verify, skip to avoid accidental deletion
                        continue
                    shutil.rmtree(skill_subdir)