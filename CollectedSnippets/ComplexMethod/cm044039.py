def assert_valid_data_record(record: dict):
    """Assert that a data record has all required fields with correct types."""
    required_keys = [
        "region",
        "country",
        "commodity",
        "attribute",
        "marketing_year",
        "value",
        "unit",
    ]
    for key in required_keys:
        assert key in record, f"Missing key: {key}"

    # Type checks
    assert record["region"] is None or isinstance(record["region"], str)
    assert isinstance(record["country"], str)
    assert isinstance(record["commodity"], str)
    assert isinstance(record["attribute"], str)
    assert isinstance(record["marketing_year"], str)
    assert isinstance(
        record["value"], float
    ), f"value should be float, got {type(record['value'])}"
    assert isinstance(record["unit"], str)