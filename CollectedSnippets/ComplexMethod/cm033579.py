def test_deepcopy(marker: Marker) -> None:
    """Verify deep copying an Marker works."""
    copied = copy.deepcopy(marker)

    assert copied is not marker

    for attribute_name in marker_attrs(marker):
        copied_value = getattr(copied, attribute_name)
        marker_value = getattr(marker, attribute_name)

        if attribute_name == '_undefined_exception':
            # The `_undefined_exception` attribute is a type, so the identity remains unchanged.
            assert copied_value is marker_value, attribute_name
        elif attribute_name == '_undefined_obj' and marker_value is jinja2.utils.missing:
            # The `_undefined_obj` attribute defaults to the `jinja2.utils.missing`, a singleton of `jinja2.utils.MissingType`.
            assert copied_value is marker_value, attribute_name
        elif type(marker_value) in (str, type(None)):
            # Values of type `str` or `None` should be equal.
            assert copied_value == marker_value, attribute_name
        else:
            # All other types should be actual copies.
            assert copied_value is not marker_value, attribute_name