def test_build_command_method_get_endpoint(method_definition):
    """Test build_command_method with a GET endpoint."""
    with (
        patch(
            "openbb_core.app.static.package_builder.MethodDefinition.is_data_processing_function",
            return_value=False,
        ),
        patch(
            "openbb_core.app.static.package_builder.MethodDefinition.is_deprecated_function",
            return_value=False,
        ),
    ):
        output = method_definition.build_command_method(
            path="/test/get",
            func=mock_get_endpoint,
            model_name=None,
        )

    assert "def get(" in output
    assert "param1: Annotated[\n            str" in output
    assert "Annotated[\n            int | None,\n" in output
    assert "This is a mock GET endpoint." in output
    assert "return self._run(" in output
    assert '"/test/get",' in output
    assert "param1=param1," in output
    assert "param2=param2," in output