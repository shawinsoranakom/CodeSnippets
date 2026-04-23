async def test_validate_schema_inputs_preserves_mcp_defaults(self, component):
        mock_tool = MagicMock()
        mock_tool.name = "run_session"
        mock_tool.args_schema = create_input_schema_from_json_schema(self._browser_use_schema())

        inputs = await component._validate_schema_inputs(mock_tool)
        input_map = {input_.name: input_ for input_ in inputs}

        assert isinstance(input_map["task"], MessageTextInput)
        assert input_map["task"].required is True

        assert isinstance(input_map["model"], MessageTextInput)
        assert input_map["model"].value == "claude-sonnet-4.6"

        assert isinstance(input_map["keep_alive"], BoolInput)
        assert input_map["keep_alive"].value is False

        assert isinstance(input_map["output_schema"], NestedDictInput)
        assert input_map["output_schema"].value is None

        assert isinstance(input_map["proxy_country"], MessageTextInput)
        assert input_map["proxy_country"].value == "us"