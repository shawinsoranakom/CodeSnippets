async def fetch_blueprint_from_github_gist_url(
    hass: HomeAssistant, url: str
) -> ImportedBlueprint:
    """Get a blueprint from a Github Gist."""
    if not url.startswith("https://gist.github.com/"):
        raise UnsupportedUrl("Not a GitHub gist url")

    parsed_url = yarl.URL(url)
    session = aiohttp_client.async_get_clientsession(hass)

    resp = await session.get(
        f"https://api.github.com/gists/{parsed_url.parts[2]}",
        headers={"Accept": "application/vnd.github.v3+json"},
        raise_for_status=True,
    )
    gist = await resp.json()

    blueprint: Blueprint | None = None
    filename: str | None = None
    content: str

    for filename, info in gist["files"].items():
        if not filename.endswith(".yaml"):
            continue

        content = info["content"]
        data = yaml_util.parse_yaml(content)

        if not is_blueprint_config(data):
            continue
        assert isinstance(data, dict)

        blueprint = Blueprint(data, schema=BLUEPRINT_SCHEMA)
        break

    if blueprint is None:
        raise HomeAssistantError(
            "No valid blueprint found in the gist. The blueprint file needs to end with"
            " '.yaml'"
        )
    if TYPE_CHECKING:
        assert isinstance(filename, str)

    return ImportedBlueprint(
        f"{gist['owner']['login']}/{filename[:-5]}", content, blueprint
    )