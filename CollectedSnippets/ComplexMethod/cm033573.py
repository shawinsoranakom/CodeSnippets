def test_dict_setdefault(template_context) -> None:
    """Ensure that setdefault templates existing values, but not defaults."""
    my_dict = _AnsibleLazyTemplateMixin._try_create(dict(invalid_template=TRUST.tag("{{ 1/0 }}"), valid_template=TRUST.tag("{{ 1 }}")))
    value_for_default = TrustedAsTemplate().tag("{{ 'default' }}")

    assert my_dict.setdefault('valid_template') == 1
    assert my_dict.setdefault('valid_template', value_for_default) == 1
    assert my_dict.setdefault('nonexistent_key', value_for_default) is value_for_default

    result = my_dict.setdefault('invalid_template', value_for_default)
    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)

    # repeat to ensure we didn't record any change
    result = my_dict.setdefault('invalid_template', value_for_default)
    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)