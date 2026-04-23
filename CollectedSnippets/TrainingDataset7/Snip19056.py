def custom_key_func(key, key_prefix, version):
    "A customized cache key function"
    return "CUSTOM-" + "-".join([key_prefix, str(version), key])