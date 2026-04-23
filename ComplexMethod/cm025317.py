async def async_handle_message(hass, message):
    """Handle a DialogFlow message."""
    _api_version = get_api_version(message)
    if _api_version is V1:
        _LOGGER.warning(
            "Dialogflow V1 API will be removed on October 23, 2019. Please change your"
            " DialogFlow settings to use the V2 api"
        )
        req = message.get("result")
        if req.get("actionIncomplete", True):
            return None

    elif _api_version is V2:
        req = message.get("queryResult")
        if req.get("allRequiredParamsPresent", False) is False:
            return None

    action = req.get("action", "")
    parameters = req.get("parameters").copy()
    parameters["dialogflow_query"] = message
    dialogflow_response = DialogflowResponse(parameters, _api_version)

    if action == "":
        raise DialogFlowError(
            "You have not defined an action in your Dialogflow intent."
        )

    intent_response = await intent.async_handle(
        hass,
        DOMAIN,
        action,
        {key: {"value": value} for key, value in parameters.items()},
    )

    if "plain" in intent_response.speech:
        dialogflow_response.add_speech(intent_response.speech["plain"]["speech"])

    return dialogflow_response.as_dict()