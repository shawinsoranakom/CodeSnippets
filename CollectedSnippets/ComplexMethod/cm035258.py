async def search_skills(
    page_id: Annotated[
        str | None,
        Query(title='Optional next_page_id from the previously returned page'),
    ] = None,
    limit: Annotated[
        int,
        Query(
            title='The max number of results in the page',
            gt=0,
            le=100,
        ),
    ] = 100,
) -> SkillPage:
    """Search / list available global and user-level skills.

    Returns skill metadata so the frontend can render a toggle list.
    """
    skills: list[SkillInfo] = []

    # Load global skills
    try:
        skills.extend(_load_skills_from_dir(GLOBAL_SKILLS_DIR, 'global'))
    except Exception as e:
        logger.warning(f'Failed to load global skills: {e}')

    # Load user-level skills
    try:
        skills.extend(_load_skills_from_dir(USER_SKILLS_DIR, 'user'))
    except Exception as e:
        logger.warning(f'Failed to load user skills: {e}')

    # Sort by source (global first), then by name
    skills.sort(key=lambda s: (s.source, s.name))

    # Apply cursor-based pagination
    start = 0
    if page_id is not None:
        for i, skill in enumerate(skills):
            if skill.name == page_id:
                start = i + 1
                break

    page = skills[start : start + limit]
    next_page_id = (
        page[-1].name if len(page) == limit and start + limit < len(skills) else None
    )

    return SkillPage(items=page, next_page_id=next_page_id)