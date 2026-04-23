def server_config(request):
    extended = request.config.getoption("--extended")
    models = request.config.getoption("--models")

    config_keys_to_test = [
        key
        for key in CONFIGS
        if (models is None or key in models)
        and (extended or not CONFIGS[key].get("extended", False))
    ]

    config_key = request.param
    if config_key not in config_keys_to_test:
        pytest.skip(f"Skipping config '{config_key}'")

    config = CONFIGS[config_key]

    if current_platform.is_rocm() and not config.get("supports_rocm", True):
        pytest.skip(
            "The {} model can't be tested on the ROCm platform".format(config["model"])
        )

    # download model and tokenizer using transformers
    snapshot_download(config["model"])
    yield CONFIGS[request.param]