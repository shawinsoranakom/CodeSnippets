def check_debug(app_configs, **kwargs):
    passed_check = not settings.DEBUG
    return [] if passed_check else [W018]