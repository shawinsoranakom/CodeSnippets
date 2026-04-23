def test_deeply_nested_pydantic_models_control_char_sanitization(self):
        """Test that control characters are sanitized in deeply nested Pydantic models."""

        # Create nested Pydantic models with control characters at different levels
        class InnerModel(BaseModel):
            deep_string: str
            value: int = 42
            metadata: dict = {}

        class MiddleModel(BaseModel):
            middle_string: str
            inner: InnerModel
            data: str

        class OuterModel(BaseModel):
            outer_string: str
            middle: MiddleModel

        # Create test data with control characters at every nesting level
        inner = InnerModel(
            deep_string="Deepest\x00Level\x08Control\x0CChars",  # Multiple control chars at deepest level
            metadata={
                "nested_key": "Nested\x1FValue\x7FDelete"
            },  # Control chars in nested dict
        )

        middle = MiddleModel(
            middle_string="Middle\x01StartOfHeading\x1FUnitSeparator",
            inner=inner,
            data="Some\x0BVerticalTab\x0EShiftOut",
        )

        outer = OuterModel(outer_string="Outer\x00Null\x07Bell", middle=middle)

        # Wrap in a dict with additional control characters
        data = {
            "top_level": "Top\x00Level\x08Backspace",
            "nested_model": outer,
            "list_with_strings": [
                "List\x00Item1",
                "List\x0CItem2\x1F",
                {"dict_in_list": "Dict\x08Value"},
            ],
        }

        # Process with SafeJson
        result = SafeJson(data)
        assert isinstance(result, Json)

        # Verify all control characters are removed at every level
        import json

        json_string = json.dumps(result.data)

        # Check that NO control characters remain anywhere
        control_chars = [
            "\x00",
            "\x01",
            "\x02",
            "\x03",
            "\x04",
            "\x05",
            "\x06",
            "\x07",
            "\x08",
            "\x0B",
            "\x0C",
            "\x0E",
            "\x0F",
            "\x10",
            "\x11",
            "\x12",
            "\x13",
            "\x14",
            "\x15",
            "\x16",
            "\x17",
            "\x18",
            "\x19",
            "\x1A",
            "\x1B",
            "\x1C",
            "\x1D",
            "\x1E",
            "\x1F",
            "\x7F",
        ]

        for char in control_chars:
            assert (
                char not in json_string
            ), f"Control character {repr(char)} found in result"

        # Verify specific sanitized content is present (control chars removed but text preserved)
        result_data = cast(dict[str, Any], result.data)

        # Top level
        assert "TopLevelBackspace" in json_string

        # Outer model level
        assert "OuterNullBell" in json_string

        # Middle model level
        assert "MiddleStartOfHeadingUnitSeparator" in json_string
        assert "SomeVerticalTabShiftOut" in json_string

        # Inner model level (deepest nesting)
        assert "DeepestLevelControlChars" in json_string

        # Nested dict in model
        assert "NestedValueDelete" in json_string

        # List items
        assert "ListItem1" in json_string
        assert "ListItem2" in json_string
        assert "DictValue" in json_string

        # Verify structure is preserved (not just converted to string)
        assert isinstance(result_data, dict)
        assert isinstance(result_data["nested_model"], dict)
        assert isinstance(result_data["nested_model"]["middle"], dict)
        assert isinstance(result_data["nested_model"]["middle"]["inner"], dict)
        assert isinstance(result_data["list_with_strings"], list)

        # Verify specific deep values are accessible and sanitized
        nested_model = cast(dict[str, Any], result_data["nested_model"])
        middle = cast(dict[str, Any], nested_model["middle"])
        inner = cast(dict[str, Any], middle["inner"])

        deep_string = inner["deep_string"]
        assert deep_string == "DeepestLevelControlChars"

        metadata = cast(dict[str, Any], inner["metadata"])
        nested_metadata = metadata["nested_key"]
        assert nested_metadata == "NestedValueDelete"