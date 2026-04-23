def gather_skills() -> list[tuple[str, Path]]:
    """Gather all skills from the skills directory.

    Returns a list of tuples (skill_name, skill_file_path).
    """
    skills: list[tuple[str, Path]] = []

    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue

        if skill_dir.name in EXCLUDED_SKILLS:
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        skill_content = skill_file.read_text()

        # Extract skill name from frontmatter if present
        skill_name = skill_dir.name
        if skill_content.startswith("---"):
            # Parse YAML frontmatter
            end_idx = skill_content.find("---", 3)
            if end_idx != -1:
                frontmatter = skill_content[3:end_idx]
                for line in frontmatter.split("\n"):
                    if line.startswith("name:"):
                        skill_name = line[5:].strip()
                        break

        skills.append((skill_name, skill_file))

    return skills