async def test_component_metadata_has_code_hash():
    """Test that built-in components have valid module and code_hash metadata."""
    result = await import_langflow_components()
    assert result is not None
    assert "components" in result
    assert len(result["components"]) > 0

    # Find first component to test
    sample_category = None
    sample_component = None
    for category, components in result["components"].items():
        if components:
            sample_category = category
            sample_component = next(iter(components.values()))
            break
    assert sample_component is not None, "No components found to test"

    # Test metadata presence - metadata should be in the 'metadata' sub-field
    assert "metadata" in sample_component, f"Metadata field missing from component in {sample_category}"