def title_logo(_: Person, title: Title | None) -> str | None:
    """Get the game logo."""

    return (
        next((to_https(i.url) for i in title.images if i.type == "Tile"), None)
        or next((to_https(i.url) for i in title.images if i.type == "Logo"), None)
        if title and title.images
        else None
    )