def _assert_create_entry_result(
    result: dict, expected_referrer: str | None = None
) -> None:
    """Assert that the result is a create entry result."""
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Google Weather"
    assert result["data"] == {
        CONF_API_KEY: "test-api-key",
        CONF_REFERRER: expected_referrer,
    }
    assert len(result["subentries"]) == 1
    subentry = result["subentries"][0]
    assert subentry["subentry_type"] == "location"
    assert subentry["title"] == "test-name"
    assert subentry["data"] == {
        CONF_LATITUDE: 10.1,
        CONF_LONGITUDE: 20.1,
    }