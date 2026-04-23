def now_playing_attributes(person: Person, title: Title | None) -> dict[str, Any]:
    """Attributes of the currently played title."""
    attributes: dict[str, Any] = {
        "short_description": None,
        "genres": None,
        "developer": None,
        "publisher": None,
        "release_date": None,
        "min_age": None,
        "achievements": None,
        "gamerscore": None,
        "progress": None,
        "platform": None,
    }

    if person.presence_details:
        active_entry = next(
            (
                d
                for d in person.presence_details
                if d.state == PRESENCE_ACTIVE and d.is_game
            ),
            None,
        ) or next(
            (d for d in person.presence_details if d.state == PRESENCE_ACTIVE),
            None,
        )

        if active_entry:
            platform = active_entry.device
            if platform == "Scarlett" and title and title.devices:
                if "Xbox360" in title.devices:
                    platform = "Xbox360"
                elif "XboxOne" in title.devices:
                    platform = "XboxOne"

            attributes["platform"] = MAP_PLATFORM_NAME.get(platform, platform)

    if not title:
        return attributes

    if title.detail is not None:
        attributes.update(
            {
                "short_description": title.detail.short_description,
                "genres": (
                    ", ".join(title.detail.genres) if title.detail.genres else None
                ),
                "developer": title.detail.developer_name,
                "publisher": title.detail.publisher_name,
                "release_date": (
                    title.detail.release_date.replace(tzinfo=UTC).date()
                    if title.detail.release_date
                    else None
                ),
                "min_age": title.detail.min_age,
            }
        )
    if (achievement := title.achievement) is not None:
        attributes.update(
            {
                "achievements": (
                    f"{achievement.current_achievements} / {achievement.total_achievements}"
                ),
                "gamerscore": (
                    f"{achievement.current_gamerscore} / {achievement.total_gamerscore}"
                ),
                "progress": f"{int(achievement.progress_percentage)} %",
            }
        )

    return attributes