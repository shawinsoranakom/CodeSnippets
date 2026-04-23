def test_schema_to_langflow_inputs():
    # Define a test Pydantic model with various field types
    class TestSchema(BaseModel):
        text_field: str = Field(title="Custom Text Title", description="A text field")
        number_field: int = Field(description="A number field")
        bool_field: bool = Field(description="A boolean field")
        dict_field: dict = Field(description="A dictionary field")
        list_field: list[str] = Field(description="A list of strings")

    # Convert schema to Langflow inputs
    inputs = schema_to_langflow_inputs(TestSchema)

    # Verify the number of inputs matches the schema fields
    expected_len = 5
    assert len(inputs) == expected_len

    # Helper function to find input by name
    def find_input(name: str) -> InputTypes | None:
        for _input in inputs:
            if _input.name == name:
                return _input
        return None

    # Test text field
    text_input = find_input("text_field")
    assert text_input.display_name == "Custom Text Title"
    assert text_input.info == "A text field"
    assert isinstance(text_input, MessageTextInput)  # Check the instance type instead of field_type

    # Test number field
    number_input = find_input("number_field")
    assert number_input.display_name == "Number Field"
    assert number_input.info == "A number field"
    assert isinstance(number_input, IntInput | FloatInput)

    # Test boolean field
    bool_input = find_input("bool_field")
    assert isinstance(bool_input, BoolInput)

    # Test dictionary field
    dict_input = find_input("dict_field")
    assert isinstance(dict_input, DictInput)

    # Test list field
    list_input = find_input("list_field")
    assert list_input.is_list is True
    assert isinstance(list_input, MessageTextInput)