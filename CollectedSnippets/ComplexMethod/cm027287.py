def get_engine(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> Provider | None:
    """Set up Amazon Polly speech component."""
    output_format = config[CONF_OUTPUT_FORMAT]
    sample_rate = config.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATES[output_format])
    if sample_rate not in SUPPORTED_SAMPLE_RATES_MAP[output_format]:
        _LOGGER.error(
            "%s is not a valid sample rate for %s", sample_rate, output_format
        )
        return None

    config[CONF_SAMPLE_RATE] = sample_rate

    profile: str | None = config.get(CONF_PROFILE_NAME)

    if profile is not None:
        boto3.setup_default_session(profile_name=profile)

    aws_config = {
        CONF_REGION: config[CONF_REGION],
        CONF_ACCESS_KEY_ID: config.get(CONF_ACCESS_KEY_ID),
        CONF_SECRET_ACCESS_KEY: config.get(CONF_SECRET_ACCESS_KEY),
        "config": botocore.config.Config(
            connect_timeout=AWS_CONF_CONNECT_TIMEOUT,
            read_timeout=AWS_CONF_READ_TIMEOUT,
            max_pool_connections=AWS_CONF_MAX_POOL_CONNECTIONS,
        ),
    }

    del config[CONF_REGION]
    del config[CONF_ACCESS_KEY_ID]
    del config[CONF_SECRET_ACCESS_KEY]

    polly_client = boto3.client("polly", **aws_config)

    supported_languages: list[str] = []

    all_voices: dict[str, dict[str, str]] = {}

    all_engines: dict[str, set[str]] = defaultdict(set)

    all_voices_req = polly_client.describe_voices()

    for voice in all_voices_req.get("Voices", []):
        voice_id: str | None = voice.get("Id")
        if voice_id is None:
            continue
        all_voices[voice_id] = voice
        language_code: str | None = voice.get("LanguageCode")
        if language_code is not None and language_code not in supported_languages:
            supported_languages.append(language_code)
        for engine in voice.get("SupportedEngines"):
            all_engines[engine].add(voice_id)

    return AmazonPollyProvider(
        polly_client, config, supported_languages, all_voices, all_engines
    )