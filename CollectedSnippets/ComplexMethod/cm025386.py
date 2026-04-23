async def async_handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: Request | MockRequest
) -> Response:
    """Handle a webhook."""
    handlers: dict[str, dict[str, Any]] = hass.data.setdefault(DOMAIN, {})

    content_stream: StreamReader | MockStreamReader
    if isinstance(request, MockRequest):
        received_from = request.mock_source
        content_stream = request.content
        method_name = request.method
    else:
        received_from = request.remote
        content_stream = request.content
        method_name = request.method

    # Always respond successfully to not give away if a hook exists or not.
    if (webhook := handlers.get(webhook_id)) is None:
        _LOGGER.info(
            "Received message for unregistered webhook %s from %s",
            webhook_id,
            received_from,
        )
        # Look at content to provide some context for received webhook
        # Limit to 64 chars to avoid flooding the log
        content = await content_stream.read(64)
        _LOGGER.debug("%s", content)
        return Response(status=HTTPStatus.OK)

    if method_name not in webhook["allowed_methods"]:
        if method_name == METH_HEAD:
            # Allow websites to verify that the URL exists.
            return Response(status=HTTPStatus.OK)

        _LOGGER.warning(
            "Webhook %s only supports %s methods but %s was received from %s",
            webhook_id,
            ",".join(webhook["allowed_methods"]),
            method_name,
            received_from,
        )
        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    if webhook["local_only"] in (True, None) and not isinstance(request, MockRequest):
        is_local = not is_cloud_connection(hass)
        if is_local:
            if TYPE_CHECKING:
                assert isinstance(request, Request)
                assert request.remote is not None

            try:
                request_remote = ip_address(request.remote)
            except ValueError:
                _LOGGER.debug("Unable to parse remote ip %s", request.remote)
                return Response(status=HTTPStatus.OK)

            is_local = network_util.is_local(request_remote)

        if not is_local:
            _LOGGER.warning("Received remote request for local webhook %s", webhook_id)
            if webhook["local_only"]:
                return Response(status=HTTPStatus.OK)
            if not webhook.get("warned_about_deprecation"):
                webhook["warned_about_deprecation"] = True
                _LOGGER.warning(
                    "Deprecation warning: "
                    "Webhook '%s' does not provide a value for local_only. "
                    "This webhook will be blocked after the 2023.11.0 release. "
                    "Use `local_only: false` to keep this webhook operating as-is",
                    webhook_id,
                )

    try:
        response: Response | None = await webhook["handler"](hass, webhook_id, request)
        if response is None:
            response = Response(status=HTTPStatus.OK)
    except Exception:
        _LOGGER.exception("Error processing webhook %s", webhook_id)
        return Response(status=HTTPStatus.OK)
    return response