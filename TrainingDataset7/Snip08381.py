def check_xframe_options_middleware(app_configs, **kwargs):
    passed_check = _xframe_middleware()
    return [] if passed_check else [W002]