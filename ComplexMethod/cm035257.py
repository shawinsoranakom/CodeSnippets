def _load_skills_from_dir(skills_dir: Path, source: str) -> list[SkillInfo]:
    """Load skill metadata from a directory of markdown files.

    Args:
        skills_dir: Path to the skills directory.
        source: Source label ('global' or 'user').

    Returns:
        List of SkillInfo objects parsed from the directory.
    """
    skills: list[SkillInfo] = []
    if not skills_dir.exists():
        return skills

    for md_file in skills_dir.rglob('*.md'):
        if md_file.name == 'README.md':
            continue

        try:
            fm = _parse_skill_frontmatter(md_file)
            if not isinstance(fm, dict):
                continue

            # Use name from frontmatter, falling back to filename stem
            name = fm.get('name') or md_file.stem

            # Determine type from frontmatter
            skill_type = fm.get('type', 'knowledge')
            triggers = fm.get('triggers') or None

            skills.append(
                SkillInfo(
                    name=name,
                    type=skill_type,
                    source=source,
                    triggers=triggers,
                )
            )
        except Exception as e:
            logger.warning(f'Failed to parse skill file {md_file}: {e}')

    return skills