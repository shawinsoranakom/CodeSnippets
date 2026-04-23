def parse_skill_md(skill_path: Path) -> Skill:
    """
    Parse a SKILL.md file and return a Skill with metadata only (Level 1).

    Args:
        skill_path: Path to the skill directory containing SKILL.md

    Returns:
        Skill object with metadata loaded

    Raises:
        SkillParseError: If the SKILL.md file cannot be parsed
        FileNotFoundError: If SKILL.md doesn't exist
    """
    skill_md_file = skill_path / "SKILL.md"

    if not skill_md_file.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md_file}")

    try:
        content = skill_md_file.read_text(encoding="utf-8")
    except Exception as e:
        raise SkillParseError(f"Failed to read SKILL.md: {e}") from e

    frontmatter_yaml, body = _extract_frontmatter(content)

    if frontmatter_yaml is None:
        raise SkillParseError(
            f"SKILL.md at {skill_path} missing required YAML frontmatter"
        )

    try:
        frontmatter_data = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        raise SkillParseError(f"Invalid YAML frontmatter in {skill_path}: {e}") from e

    if not isinstance(frontmatter_data, dict):
        raise SkillParseError(
            f"YAML frontmatter in {skill_path} must be a mapping, "
            f"got {type(frontmatter_data).__name__}"
        )

    # Handle nested metadata field if present
    if "metadata" in frontmatter_data:
        metadata_section = frontmatter_data.pop("metadata")
        if isinstance(metadata_section, dict):
            # Merge metadata fields into top level (author, version, tags)
            for key in ["author", "version", "tags"]:
                if key in metadata_section and key not in frontmatter_data:
                    frontmatter_data[key] = metadata_section[key]

    try:
        metadata = SkillMetadata(**frontmatter_data)
    except ValidationError as e:
        raise SkillParseError(
            f"Invalid metadata in SKILL.md at {skill_path}: {e}"
        ) from e

    return Skill(
        path=skill_path,
        metadata=metadata,
        content=None,  # Content not loaded at Level 1
        load_level=SkillLoadLevel.METADATA,
    )