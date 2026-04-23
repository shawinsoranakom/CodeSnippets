def generate_fingerprint(options: Dict[str, Any] = None) -> str:
    if options is None:
        options = {}

    config = DEFAULT_TEMPLATE.copy()

    # platform preset
    platform = options.get("platform")
    if platform in PLATFORM_PRESETS:
        config.update(PLATFORM_PRESETS[platform])

    # screen preset
    screen = options.get("screen")
    if screen in SCREEN_PRESETS:
        config["screenInfo"] = SCREEN_PRESETS[screen]

    # language preset
    locale = options.get("locale")
    if locale in LANGUAGE_PRESETS:
        config.update(LANGUAGE_PRESETS[locale])

    # custom overrides
    if "custom" in options and isinstance(options["custom"], dict):
        config.update(options["custom"])

    device_id = options.get("deviceId") or generate_device_id()
    current_timestamp = int(time.time() * 1000)

    plugin_hash = generate_hash()
    canvas_hash = generate_hash()
    ua_hash1 = generate_hash()
    ua_hash2 = generate_hash()
    url_hash = generate_hash()
    doc_hash = random.randint(10, 100)

    fields: List[Any] = [
        device_id,
        config["sdkVersion"],
        config["initTimestamp"],
        config["field3"],
        config["field4"],
        config["language"],
        config["timezoneOffset"],
        config["colorDepth"],
        config["screenInfo"],
        config["field9"],
        config["platform"],
        config["field11"],
        config["webglRenderer"],
        config["field13"],
        config["field14"],
        config["field15"],
        f'{config["pluginCount"]}|{plugin_hash}',
        canvas_hash,
        ua_hash1,
        "1",
        "0",
        "1",
        "0",
        config["mode"],
        "0",
        "0",
        "0",
        "416",
        config["vendor"],
        config["field29"],
        config["touchInfo"],
        ua_hash2,
        config["field32"],
        current_timestamp,
        url_hash,
        config["field35"],
        doc_hash,
    ]

    return "^".join(map(str, fields))