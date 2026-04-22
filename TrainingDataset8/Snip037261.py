def _create_section(section: str, description: str) -> None:
    """Create a config section and store it globally in this module."""
    assert section not in _section_descriptions, (
        'Cannot define section "%s" twice.' % section
    )
    _section_descriptions[section] = description