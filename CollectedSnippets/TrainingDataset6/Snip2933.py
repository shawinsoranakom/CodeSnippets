def test_invalid_type_value() -> None:
    """Test that Schema raises ValueError for invalid type values."""
    with pytest.raises(ValueError, match="2 validation errors for Schema"):
        Schema(type=True)