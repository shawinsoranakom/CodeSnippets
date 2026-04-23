def localize_settings_changed(*, setting, **kwargs):
    if setting in FORMAT_SETTINGS or setting == "USE_THOUSAND_SEPARATOR":
        reset_format_cache()