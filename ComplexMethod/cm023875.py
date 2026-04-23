async def perform_put_light_state(
    hass_hue: HomeAssistant,
    client: TestClient,
    entity_id: str,
    is_on: bool,
    *,
    brightness: int | None = None,
    content_type: str = CONTENT_TYPE_JSON,
    hue: int | None = None,
    saturation: int | None = None,
    color_temp: int | None = None,
    with_state: bool = True,
    xy: tuple[float, float] | None = None,
    transitiontime: int | None = None,
):
    """Test the setting of a light state."""
    req_headers = {"Content-Type": content_type}

    data = {}

    if with_state:
        data[HUE_API_STATE_ON] = is_on

    if brightness is not None:
        data[HUE_API_STATE_BRI] = brightness
    if hue is not None:
        data[HUE_API_STATE_HUE] = hue
    if saturation is not None:
        data[HUE_API_STATE_SAT] = saturation
    if xy is not None:
        data[HUE_API_STATE_XY] = xy
    if color_temp is not None:
        data[HUE_API_STATE_CT] = color_temp
    if transitiontime is not None:
        data[HUE_API_STATE_TRANSITION] = transitiontime

    entity_number = ENTITY_NUMBERS_BY_ID[entity_id]
    result = await client.put(
        f"/api/username/lights/{entity_number}/state",
        headers=req_headers,
        data=json.dumps(data).encode(),
    )

    # Wait until state change is complete before continuing
    await hass_hue.async_block_till_done()

    return result