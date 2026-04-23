def process_before_send(
    hass: HomeAssistant,
    options: Mapping[str, Any],
    channel: str,
    huuid: str,
    system_info: dict[str, bool | str],
    custom_components: dict[str, Integration],
    event: dict[str, Any],
    hint: dict[str, Any],
):
    """Process a Sentry event before sending it to Sentry."""
    # Filter out handled events by default
    if (
        "tags" in event
        and event["tags"].get("handled", "no") == "yes"
        and not options.get(CONF_EVENT_HANDLED)
    ):
        return None

    # Additional tags to add to the event
    additional_tags = {
        "channel": channel,
        "installation_type": system_info["installation_type"],
        "uuid": huuid,
    }

    # Find out all integrations in use, filter "auth", because it
    # triggers security rules, hiding all data.
    integrations = [
        integration
        for integration in hass.config.components
        if integration != "auth" and "." not in integration
    ]

    # Add additional tags based on what caused the event.
    if (platform := entity_platform.current_platform.get()) is not None:
        # This event happened in a platform
        additional_tags["custom_component"] = "no"
        additional_tags["integration"] = platform.platform_name
        additional_tags["platform"] = platform.domain
    elif "logger" in event:
        # Logger event, try to get integration information from the logger name.
        matches = LOGGER_INFO_REGEX.findall(event["logger"])
        if matches:
            group1, group2, group3, group4 = matches[0]
            # Handle the "homeassistant." package differently
            if group1 == "homeassistant" and group2 and group3:
                if group2 == "components":
                    # This logger is from a component
                    additional_tags["custom_component"] = "no"
                    additional_tags["integration"] = group3
                    if group4 and group4 in ENTITY_COMPONENTS:
                        additional_tags["platform"] = group4
                else:
                    # Not a component, could be helper, or something else.
                    additional_tags[group2] = group3
            else:
                # Not the "homeassistant" package, this third-party
                if not options.get(CONF_EVENT_THIRD_PARTY_PACKAGES):
                    return None
                additional_tags["package"] = group1

    # If this event is caused by an integration, add a tag if this
    # integration is custom or not.
    if (
        "integration" in additional_tags
        and additional_tags["integration"] in custom_components
    ):
        if not options.get(CONF_EVENT_CUSTOM_COMPONENTS):
            return None
        additional_tags["custom_component"] = "yes"

    # Update event with the additional tags
    event.setdefault("tags", {}).update(additional_tags)

    # Set user context to the installation UUID
    event.setdefault("user", {}).update({"id": huuid})

    # Update event data with Home Assistant Context
    event.setdefault("contexts", {}).update(
        {
            "Home Assistant": {
                "channel": channel,
                "custom_components": "\n".join(sorted(custom_components)),
                "integrations": "\n".join(sorted(integrations)),
                **system_info,
            },
        }
    )
    return event