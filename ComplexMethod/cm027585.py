def _positive_time_period_template_complex(value: Any) -> Any:
    """Do basic validation of a positive time period expressed as a templated dict."""
    if not isinstance(value, dict) or not value:
        raise vol.Invalid("template should be a dict")
    for key, element in value.items():
        if not isinstance(key, str):
            raise vol.Invalid("key should be a string")
        if not template_helper.is_template_string(key):
            vol.In(_TIME_PERIOD_DICT_KEYS)(key)
        if not isinstance(element, str) or (
            isinstance(element, str) and not template_helper.is_template_string(element)
        ):
            vol.All(vol.Coerce(float), vol.Range(min=0))(element)
    return template_complex(value)