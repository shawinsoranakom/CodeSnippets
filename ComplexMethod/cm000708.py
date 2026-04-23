async def test_dynamic_field_description_generation():
    """Test that dynamic field descriptions are generated correctly."""
    # Test dictionary field description
    desc = get_dynamic_field_description("values_#_name")
    assert "Dictionary field 'name' for base field 'values'" in desc
    assert "values['name']" in desc

    # Test list field description
    desc = get_dynamic_field_description("items_$_0")
    assert "List item 0 for base field 'items'" in desc
    assert "items[0]" in desc

    # Test object field description
    desc = get_dynamic_field_description("user_@_email")
    assert "Object attribute 'email' for base field 'user'" in desc
    assert "user.email" in desc

    # Test regular field fallback
    desc = get_dynamic_field_description("regular_field")
    assert desc == "Value for regular_field"