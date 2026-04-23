async def async_handle_intent(
    hass: HomeAssistant, message: dict[str, Any]
) -> dict[str, Any]:
    """Handle an intent request.

    Raises:
     - intent.UnknownIntent
     - intent.InvalidSlotInfo
     - intent.IntentError

    """
    req = message["request"]
    alexa_intent_info = req.get("intent")
    alexa_response = AlexaIntentResponse(hass, alexa_intent_info)

    if req["type"] == "LaunchRequest":
        intent_name = (
            message.get("session", {}).get("application", {}).get("applicationId")
        )
    elif req["type"] == "SessionEndedRequest":
        app_id = message.get("session", {}).get("application", {}).get("applicationId")
        intent_name = f"{app_id}.{req['type']}"
        alexa_response.variables["reason"] = req["reason"]
        alexa_response.variables["error"] = req.get("error")
    else:
        intent_name = alexa_intent_info["name"]

    intent_response = await intent.async_handle(
        hass,
        DOMAIN,
        intent_name,
        {key: {"value": value} for key, value in alexa_response.variables.items()},
    )

    for intent_speech, alexa_speech in SPEECH_MAPPINGS.items():
        if intent_speech in intent_response.speech:
            alexa_response.add_speech(
                alexa_speech, intent_response.speech[intent_speech]["speech"]
            )
        if intent_speech in intent_response.reprompt:
            alexa_response.add_reprompt(
                alexa_speech, intent_response.reprompt[intent_speech]["reprompt"]
            )

    if "simple" in intent_response.card:
        alexa_response.add_card(
            CardType.simple,
            intent_response.card["simple"]["title"],
            intent_response.card["simple"]["content"],
        )

    return alexa_response.as_dict()