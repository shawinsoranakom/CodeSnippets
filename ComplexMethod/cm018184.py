def _assert_extract_from_target_command_result(
    msg: dict[str, Any],
    entities: set[str] | None = None,
    devices: set[str] | None = None,
    areas: set[str] | None = None,
    missing_devices: set[str] | None = None,
    missing_areas: set[str] | None = None,
    missing_labels: set[str] | None = None,
    missing_floors: set[str] | None = None,
) -> None:
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    result = msg["result"]
    assert set(result["referenced_entities"]) == (entities or set())
    assert set(result["referenced_devices"]) == (devices or set())
    assert set(result["referenced_areas"]) == (areas or set())
    assert set(result["missing_devices"]) == (missing_devices or set())
    assert set(result["missing_areas"]) == (missing_areas or set())
    assert set(result["missing_floors"]) == (missing_floors or set())
    assert set(result["missing_labels"]) == (missing_labels or set())