def _migrate_legacy_kimi_dotted_skills(skills_dir: Path) -> tuple[int, int]:
    """Migrate legacy Kimi dotted skill dirs (speckit.xxx) to hyphenated format.

    Returns ``(migrated_count, removed_count)``.
    """
    if not skills_dir.is_dir():
        return (0, 0)

    migrated_count = 0
    removed_count = 0

    for legacy_dir in sorted(skills_dir.glob("speckit.*")):
        if not legacy_dir.is_dir():
            continue
        if not (legacy_dir / "SKILL.md").exists():
            continue

        suffix = legacy_dir.name[len("speckit."):]
        if not suffix:
            continue

        target_dir = skills_dir / f"speckit-{suffix.replace('.', '-')}"

        if not target_dir.exists():
            shutil.move(str(legacy_dir), str(target_dir))
            migrated_count += 1
            continue

        # Target exists — only remove legacy if SKILL.md is identical
        target_skill = target_dir / "SKILL.md"
        legacy_skill = legacy_dir / "SKILL.md"
        if target_skill.is_file():
            try:
                if target_skill.read_bytes() == legacy_skill.read_bytes():
                    has_extra = any(
                        child.name != "SKILL.md" for child in legacy_dir.iterdir()
                    )
                    if not has_extra:
                        shutil.rmtree(legacy_dir)
                        removed_count += 1
            except OSError:
                pass

    return (migrated_count, removed_count)