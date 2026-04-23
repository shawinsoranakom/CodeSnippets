def test_dict_popitem(template_context):
    """Ensure popitem respects insertion order, templating of values, and that templating occurs before the collection is mutated."""
    my_dict = _AnsibleLazyTemplateMixin._try_create(dict(
        also_valid_template=TRUST.tag("{{ 0 }}"),
        busted_template=TRUST.tag("{{ 1 / 0 }}"),
        valid_template=TRUST.tag("{{ 1 }}"),
    ))

    assert my_dict.popitem() == ('valid_template', 1)

    with JinjaCallContext(accept_lazy_markers=False):
        with pytest.raises(MarkerError):
            my_dict.popitem()

    assert 'busted_template' in my_dict

    raw_result = my_dict.popitem()

    assert isinstance(raw_result, tuple)

    key, result = raw_result

    assert key == 'busted_template'
    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)

    assert my_dict.popitem() == ('also_valid_template', 0)

    with pytest.raises(KeyError):
        my_dict.popitem()