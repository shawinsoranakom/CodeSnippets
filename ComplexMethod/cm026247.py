async def execute_service(
    entry_data: RuntimeEntryData,
    service: UserService,
    call: ServiceCall,
    *,
    supports_response: SupportsResponseType,
) -> ServiceResponse:
    """Execute a service on a node and optionally wait for response."""
    # Determine if we should wait for a response
    # NONE: fire and forget
    # OPTIONAL/ONLY/STATUS: always wait for success/error confirmation
    wait_for_response = supports_response != SupportsResponseType.NONE

    if not wait_for_response:
        # Fire and forget - no response expected
        try:
            await entry_data.client.execute_service(service, call.data)
        except APIConnectionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_call_failed",
                translation_placeholders={
                    "call_name": service.name,
                    "device_name": entry_data.name,
                    "error": str(err),
                },
            ) from err
        else:
            return None

    # Determine if we need response_data from ESPHome
    # ONLY: always need response_data
    # OPTIONAL: only if caller requested it
    # STATUS: never need response_data (just success/error)
    need_response_data = supports_response == SupportsResponseType.ONLY or (
        supports_response == SupportsResponseType.OPTIONAL and call.return_response
    )

    try:
        response: (
            ExecuteServiceResponse | None
        ) = await entry_data.client.execute_service(
            service,
            call.data,
            return_response=need_response_data,
        )
    except APIConnectionError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="action_call_failed",
            translation_placeholders={
                "call_name": service.name,
                "device_name": entry_data.name,
                "error": str(err),
            },
        ) from err
    except TimeoutError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="action_call_timeout",
            translation_placeholders={
                "call_name": service.name,
                "device_name": entry_data.name,
            },
        ) from err

    assert response is not None

    if not response.success:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="action_call_failed",
            translation_placeholders={
                "call_name": service.name,
                "device_name": entry_data.name,
                "error": response.error_message,
            },
        )

    # Parse and return response data as JSON if we requested it
    if need_response_data and response.response_data:
        try:
            return json_loads_object(response.response_data)
        except ValueError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_call_failed",
                translation_placeholders={
                    "call_name": service.name,
                    "device_name": entry_data.name,
                    "error": f"Invalid JSON response: {err}",
                },
            ) from err
    return None