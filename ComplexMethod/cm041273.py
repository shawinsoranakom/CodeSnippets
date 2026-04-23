def get_localstack_config() -> dict:
    result = {}
    for k, v in inspect.getmembers(config):
        if k in EXCLUDE_CONFIG_KEYS:
            continue
        if inspect.isbuiltin(v):
            continue
        if inspect.isfunction(v):
            continue
        if inspect.ismodule(v):
            continue
        if inspect.isclass(v):
            continue
        if "typing." in str(type(v)):
            continue
        if k == "GATEWAY_LISTEN":
            result[k] = config.GATEWAY_LISTEN
            continue

        if hasattr(v, "__dict__"):
            result[k] = v.__dict__
        else:
            result[k] = v

    return result