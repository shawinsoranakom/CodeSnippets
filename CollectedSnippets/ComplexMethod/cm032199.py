def is_any_api_key(key):
    # key 一般只包含字母、数字、下划线、逗号、中划线
    if not re.match(r"^[a-zA-Z0-9_\-,]+$", key):
        # 如果配置了 CUSTOM_API_KEY_PATTERN，再检查以下以免误杀
        if CUSTOM_API_KEY_PATTERN := get_conf('CUSTOM_API_KEY_PATTERN'):
            return bool(re.match(CUSTOM_API_KEY_PATTERN, key))
        return False

    if ',' in key:
        keys = key.split(',')
        for k in keys:
            if is_any_api_key(k): return True
        return False
    else:
        return is_openai_api_key(key) or is_api2d_key(key) or is_azure_api_key(key) or is_cohere_api_key(key)