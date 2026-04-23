def get_attribute_points(
    user: UserData, content: ContentData, attribute: str
) -> dict[str, float]:
    """Get modifiers contributing to STR/INT/CON/PER attributes."""

    equipment = sum(
        getattr(stats, attribute)
        for gear in fields(user.items.gear.equipped)
        if (equipped := getattr(user.items.gear.equipped, gear.name))
        and (stats := content.gear.flat[equipped])
    )

    class_bonus = sum(
        getattr(stats, attribute) / 2
        for gear in fields(user.items.gear.equipped)
        if (equipped := getattr(user.items.gear.equipped, gear.name))
        and (stats := content.gear.flat[equipped])
        and stats.klass == user.stats.Class
    )
    if TYPE_CHECKING:
        assert user.stats.lvl

    return {
        "level": min(floor(user.stats.lvl / 2), 50),
        "equipment": equipment,
        "class": class_bonus,
        "allocated": getattr(user.stats, attribute),
        "buffs": getattr(user.stats.buffs, attribute),
    }