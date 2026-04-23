def test_include_raw_returns_raw_and_parsed_on_success(self) -> None:
        """Test that `include_raw=True` returns raw message, parsed output, no error."""
        model = _make_model()
        model.client = MagicMock()
        model.client.chat.send.return_value = _make_sdk_response(_TOOL_RESPONSE_DICT)

        structured = model.with_structured_output(
            GetWeather, method="function_calling", include_raw=True
        )
        result = structured.invoke("weather in SF")
        assert isinstance(result, dict)
        assert "raw" in result
        assert "parsed" in result
        assert "parsing_error" in result
        assert isinstance(result["raw"], AIMessage)
        assert result["parsing_error"] is None
        # PydanticToolsParser returns a Pydantic instance, not a dict
        assert isinstance(result["parsed"], GetWeather)
        assert result["parsed"].location == "San Francisco"