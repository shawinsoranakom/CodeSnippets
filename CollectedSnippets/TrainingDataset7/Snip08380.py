def check_security_middleware(app_configs, **kwargs):
    passed_check = _security_middleware()
    return [] if passed_check else [W001]