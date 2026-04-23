def _mocked_feature(
    id: str,
    *,
    require_fixture=False,
    value: Any = UNDEFINED,
    name=None,
    type_=None,
    category=None,
    precision_hint=None,
    choices=None,
    unit=None,
    minimum_value=None,
    maximum_value=None,
    expected_module_key=None,
) -> Feature:
    """Get a mocked feature.

    If kwargs are provided they will override the attributes for any features defined in fixtures.json
    """
    feature = MagicMock(spec=Feature, name=f"Mocked {id} feature")
    feature.id = id
    feature.name = name or id.upper()
    feature.set_value = AsyncMock()
    if fixture := FEATURES_FIXTURE.get(id):
        # copy the fixture so tests do not interfere with each other
        fixture = dict(fixture)

        if enum_type := fixture.get("enum_type"):
            val = FIXTURE_ENUM_TYPES[enum_type](fixture["value"])
            fixture["value"] = val
        if timedelta_type := fixture.get("timedelta_type"):
            fixture["value"] = timedelta(**{timedelta_type: fixture["value"]})

        if unit_enum_type := fixture.get("unit_enum_type"):
            val = FIXTURE_ENUM_TYPES[unit_enum_type](fixture["unit"])
            fixture["unit"] = val

    else:
        assert require_fixture is False, (
            f"No fixture defined for feature {id} and require_fixture is True"
        )
        assert value is not UNDEFINED, (
            f"Value must be provided if feature {id} not defined in features.json"
        )
        fixture = {"value": value, "category": "Primary", "type": "Sensor"}

    if value is not UNDEFINED:
        fixture["value"] = value
    feature.value = fixture["value"]

    feature.type = type_ or Feature.Type[fixture["type"]]
    feature.category = category or Feature.Category[fixture["category"]]

    # sensor
    feature.precision_hint = precision_hint or fixture.get("precision_hint")
    feature.unit = unit or fixture.get("unit")

    # number
    min_val = minimum_value or fixture.get("minimum_value")
    feature.minimum_value = 0 if min_val is None else min_val
    max_val = maximum_value or fixture.get("maximum_value")
    feature.maximum_value = 2**16 if max_val is None else max_val

    # select
    feature.choices = choices or fixture.get("choices")

    # module features are accessed from a module via get_feature which is
    # keyed on the module attribute name. Usually this is the same as the
    # feature.id but not always. module_key indicates the key of the feature
    # in the module.
    feature.expected_module_key = (
        mod_key
        if (mod_key := fixture.get("expected_module_key", expected_module_key))
        else None
    )

    return feature