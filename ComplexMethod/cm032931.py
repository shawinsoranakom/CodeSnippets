def show_configs():
    msg = f"Current configs, from {conf_realpath(SERVICE_CONF)}:"
    for k, v in CONFIGS.items():
        if isinstance(v, dict):
            if "password" in v:
                v = copy.deepcopy(v)
                v["password"] = "*" * 8
            if "access_key" in v:
                v = copy.deepcopy(v)
                v["access_key"] = "*" * 8
            if "secret_key" in v:
                v = copy.deepcopy(v)
                v["secret_key"] = "*" * 8
            if "secret" in v:
                v = copy.deepcopy(v)
                v["secret"] = "*" * 8
            if "sas_token" in v:
                v = copy.deepcopy(v)
                v["sas_token"] = "*" * 8
            if "oauth" in k:
                v = copy.deepcopy(v)
                for key, val in v.items():
                    if "client_secret" in val:
                        val["client_secret"] = "*" * 8
            if "authentication" in k:
                v = copy.deepcopy(v)
                for key, val in v.items():
                    if isinstance(val, dict) and "http_secret_key" in val:
                        val["http_secret_key"] = "*" * 8
        msg += f"\n\t{k}: {v}"
    logging.info(msg)