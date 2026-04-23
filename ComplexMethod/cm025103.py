def test_result_as_boolean(hass: HomeAssistant) -> None:
    """Test converting a template result to a boolean."""

    assert template.result_as_boolean(True) is True
    assert template.result_as_boolean(" 1 ") is True
    assert template.result_as_boolean(" true ") is True
    assert template.result_as_boolean(" TrUE ") is True
    assert template.result_as_boolean(" YeS ") is True
    assert template.result_as_boolean(" On ") is True
    assert template.result_as_boolean(" Enable ") is True
    assert template.result_as_boolean(1) is True
    assert template.result_as_boolean(-1) is True
    assert template.result_as_boolean(500) is True
    assert template.result_as_boolean(0.5) is True
    assert template.result_as_boolean(0.389) is True
    assert template.result_as_boolean(35) is True

    assert template.result_as_boolean(False) is False
    assert template.result_as_boolean(" 0 ") is False
    assert template.result_as_boolean(" false ") is False
    assert template.result_as_boolean(" FaLsE ") is False
    assert template.result_as_boolean(" no ") is False
    assert template.result_as_boolean(" off ") is False
    assert template.result_as_boolean(" disable ") is False
    assert template.result_as_boolean(0) is False
    assert template.result_as_boolean(0.0) is False
    assert template.result_as_boolean("0.00") is False
    assert template.result_as_boolean(None) is False