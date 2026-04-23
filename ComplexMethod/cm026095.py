async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> AWSNotify | None:
    """Get the AWS notification service."""
    if discovery_info is None:
        _LOGGER.error("Please config aws notify platform in aws component")
        return None

    session = None

    conf = discovery_info

    service = conf[CONF_SERVICE]
    region_name = conf[CONF_REGION]

    available_regions = await get_available_regions(hass, service)
    if region_name not in available_regions:
        _LOGGER.error(
            "Region %s is not available for %s service, must in %s",
            region_name,
            service,
            available_regions,
        )
        return None

    aws_config = conf.copy()

    del aws_config[CONF_SERVICE]
    del aws_config[CONF_REGION]
    if CONF_PLATFORM in aws_config:
        del aws_config[CONF_PLATFORM]
    if CONF_NAME in aws_config:
        del aws_config[CONF_NAME]
    if CONF_CONTEXT in aws_config:
        del aws_config[CONF_CONTEXT]

    sessions = hass.data[DATA_AWS].sessions

    if not aws_config:
        # no platform config, use the first aws component credential instead
        if sessions:
            session = next(iter(sessions.values()))
        else:
            _LOGGER.error("Missing aws credential for %s", config[CONF_NAME])
            return None

    if session is None:
        credential_name = aws_config.get(CONF_CREDENTIAL_NAME)
        if credential_name is not None:
            session = sessions.get(credential_name)
            if session is None:
                _LOGGER.warning("No available aws session for %s", credential_name)
            del aws_config[CONF_CREDENTIAL_NAME]

    if session is None:
        if (profile := aws_config.get(CONF_PROFILE_NAME)) is not None:
            session = AioSession(profile=profile)
            del aws_config[CONF_PROFILE_NAME]
        else:
            session = AioSession()

    aws_config[CONF_REGION] = region_name

    if service == "lambda":
        context_str = json.dumps(
            {"custom": conf.get(CONF_CONTEXT, {})}, cls=JSONEncoder
        )
        context_b64 = base64.b64encode(context_str.encode("utf-8"))
        context = context_b64.decode("utf-8")
        return AWSLambda(session, aws_config, context)

    if service == "sns":
        return AWSSNS(session, aws_config)

    if service == "sqs":
        return AWSSQS(session, aws_config)

    if service == "events":
        return AWSEventBridge(session, aws_config)

    # should not reach here since service was checked in schema
    return None