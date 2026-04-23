def _extract_blueprint_from_community_topic(
    url: str,
    topic: dict,
) -> ImportedBlueprint:
    """Extract a blueprint from a community post JSON.

    Async friendly.
    """
    block_content: str
    blueprint = None
    post = topic["post_stream"]["posts"][0]

    for match in COMMUNITY_CODE_BLOCK.finditer(post["cooked"]):
        block_syntax, block_content = match.groups()

        if block_syntax not in ("auto", "yaml"):
            continue

        block_content = html.unescape(block_content.strip())

        try:
            data = yaml_util.parse_yaml(block_content)
        except HomeAssistantError:
            if block_syntax == "yaml":
                raise

            continue

        if not is_blueprint_config(data):
            continue
        assert isinstance(data, dict)

        blueprint = Blueprint(data, schema=BLUEPRINT_SCHEMA)
        break

    if blueprint is None:
        raise HomeAssistantError(
            "No valid blueprint found in the topic. Blueprint syntax blocks need to be"
            " marked as YAML or no syntax."
        )

    return ImportedBlueprint(
        f"{post['username']}/{topic['slug']}", block_content, blueprint
    )