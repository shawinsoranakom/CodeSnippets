async def test_controller_flow(
    hass: HomeAssistant,
    mock_setup: Mock,
    expected_config_entry: dict[str, str],
    expected_unique_id: int | None,
) -> None:
    """Test the controller is setup correctly."""

    result = await complete_flow(hass)
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == HOST
    assert "result" in result
    assert dict(result["result"].data) == expected_config_entry
    assert result["result"].options == {ATTR_DURATION: 6}
    assert result["result"].unique_id == expected_unique_id

    assert len(mock_setup.mock_calls) == 1