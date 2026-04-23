async def handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: web.Request
) -> web.Response:
    """Handle webhook callback.

    iOS sets the "topic" as part of the payload.
    Android does not set a topic but adds headers to the request.
    """
    context = hass.data[DOMAIN]["context"]
    topic_base = re.sub("/#$", "", context.mqtt_topic)

    try:
        message = await request.json()
    except ValueError:
        _LOGGER.warning("Received invalid JSON from OwnTracks")
        return web.json_response([])

    # Android doesn't populate topic
    if "topic" not in message:
        headers = request.headers
        user = headers.get("X-Limit-U")
        device = headers.get("X-Limit-D", user)

        if user:
            message["topic"] = f"{topic_base}/{user}/{device}"

        elif message["_type"] != "encrypted":
            _LOGGER.warning(
                "No topic or user found in message. If on Android,"
                " set a username in Connection -> Identification"
            )
            # Keep it as a 200 response so the incorrect packet is discarded
            return web.json_response([])

    async_dispatcher_send(hass, DOMAIN, hass, context, message)

    response = [
        {
            "_type": "location",
            "lat": person.attributes["latitude"],
            "lon": person.attributes["longitude"],
            "tid": "".join(p[0] for p in person.name.split(" ")[:2]),
            "tst": int(person.last_updated.timestamp()),
        }
        for person in hass.states.async_all("person")
        if "latitude" in person.attributes and "longitude" in person.attributes
    ]

    if message["_type"] == "encrypted" and context.secret:
        return web.json_response(
            {
                "_type": "encrypted",
                "data": encrypt_message(
                    context.secret, message["topic"], json.dumps(response)
                ),
            }
        )

    return web.json_response(response)