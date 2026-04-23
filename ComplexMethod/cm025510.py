def async_request_config(
    hass: HomeAssistant,
    name: str,
    callback: ConfiguratorCallback | None = None,
    description: str | None = None,
    description_image: str | None = None,
    submit_caption: str | None = None,
    fields: list[dict[str, str]] | None = None,
    link_name: str | None = None,
    link_url: str | None = None,
    entity_picture: str | None = None,
) -> str:
    """Create a new request for configuration.

    Will return an ID to be used for sequent calls.
    """
    if description and link_name is not None and link_url is not None:
        description += f"\n\n[{link_name}]({link_url})"

    if description and description_image is not None:
        description += f"\n\n![Description image]({description_image})"

    if (instance := hass.data.get(_KEY_INSTANCE)) is None:
        instance = hass.data[_KEY_INSTANCE] = Configurator(hass)

    request_id = instance.async_request_config(
        name, callback, description, submit_caption, fields, entity_picture
    )

    if DATA_REQUESTS not in hass.data:
        hass.data[DATA_REQUESTS] = {}

    _get_requests(hass)[request_id] = instance

    return request_id