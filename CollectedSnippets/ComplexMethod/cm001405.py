def discover_skills(directories: list[Path]) -> list[Skill]:
    """
    Discover all skills in the given directories.

    Args:
        directories: List of directories to search for skills

    Returns:
        List of Skill objects with metadata loaded (Level 1)
    """
    skills: list[Skill] = []
    seen_names: set[str] = set()

    for directory in directories:
        if not directory.exists():
            logger.debug(f"Skill directory does not exist: {directory}")
            continue

        if not directory.is_dir():
            logger.warning(f"Skill path is not a directory: {directory}")
            continue

        for item in directory.iterdir():
            if not item.is_dir():
                continue

            skill_md = item / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                skill = parse_skill_md(item)

                # Skip duplicates (first occurrence wins)
                if skill.metadata.name in seen_names:
                    logger.warning(
                        f"Duplicate skill name '{skill.metadata.name}' "
                        f"found at {item}, skipping"
                    )
                    continue

                seen_names.add(skill.metadata.name)
                skills.append(skill)
                logger.debug(f"Discovered skill: {skill.metadata.name} at {item}")

            except (SkillParseError, FileNotFoundError) as e:
                logger.warning(f"Failed to parse skill at {item}: {e}")
                continue

    return skills