def _test_selector(
    selector_type: str,
    schema: dict | None,
    valid_selections: Iterable[Any],
    invalid_selections: Iterable[Any],
    converter: Callable[[Any], Any] | None = None,
):
    """Help test a selector."""

    def default_converter(x):
        return x

    if converter is None:
        converter = default_converter

    # Validate selector configuration
    config = {selector_type: schema}
    selector.validate_selector(config)
    selector_instance = selector.selector(config)
    assert selector_instance == selector.selector(config)
    assert selector_instance != 5
    # We do not allow enums in the config, as they cannot serialize
    assert not any(isinstance(val, Enum) for val in selector_instance.config.values())

    # Use selector in schema and validate
    vol_schema = vol.Schema({"selection": selector_instance})
    for selection in valid_selections:
        assert vol_schema({"selection": selection}) == {
            "selection": converter(selection)
        }
    for selection in invalid_selections:
        with pytest.raises(vol.Invalid):
            vol_schema({"selection": selection})

    # Serialize selector
    selector_instance = selector.selector({selector_type: schema})
    assert selector_instance.serialize() == {
        "selector": {selector_type: selector_instance.config}
    }
    # Test serialized selector can be dumped to YAML
    yaml_util.dump(selector_instance.serialize())