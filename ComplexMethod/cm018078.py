async def test_form_shows_with_added_suggested_values(manager: MockFlowManager) -> None:
    """Test that we can show a form with suggested values."""

    def compare_schemas(schema: vol.Schema, expected_schema: vol.Schema) -> None:
        """Compare two schemas."""
        assert schema.schema is not expected_schema.schema

        assert list(schema.schema) == list(expected_schema.schema)

        for key, validator in schema.schema.items():
            if isinstance(validator, data_entry_flow.section):
                assert validator.schema == expected_schema.schema[key].schema
                continue
            assert validator == expected_schema.schema[key]

    schema = vol.Schema(
        {
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("section_1"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional("full_name"): str,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            data_schema = self.add_suggested_values_to_schema(
                schema,
                user_input,
            )
            return self.async_show_form(
                step_id="init",
                data_schema=data_schema,
            )

    form = await manager.async_init(
        "test",
        data={
            "username": "doej",
            "password": "verySecret1",
            "section_1": {"full_name": "John Doe"},
        },
    )
    assert form["type"] == data_entry_flow.FlowResultType.FORM
    assert form["data_schema"].schema is not schema.schema
    assert form["data_schema"].schema != schema.schema
    compare_schemas(form["data_schema"], schema)
    markers = list(form["data_schema"].schema)
    assert len(markers) == 3
    assert markers[0] == "username"
    assert markers[0].description == {"suggested_value": "doej"}
    assert markers[1] == "password"
    assert markers[1].description == {"suggested_value": "verySecret1"}
    assert markers[2] == "section_1"
    section_validator = form["data_schema"].schema["section_1"]
    assert isinstance(section_validator, data_entry_flow.section)
    # The section instance was copied
    assert section_validator is not schema.schema["section_1"]
    # The section schema instance was copied
    assert section_validator.schema is not schema.schema["section_1"].schema
    assert section_validator.schema == schema.schema["section_1"].schema
    section_markers = list(section_validator.schema.schema)
    assert len(section_markers) == 1
    assert section_markers[0] == "full_name"
    assert section_markers[0].description == {"suggested_value": "John Doe"}

    # Test again without suggested values to make sure we're not mutating the schema
    form = await manager.async_init(
        "test",
    )
    assert form["type"] == data_entry_flow.FlowResultType.FORM
    assert form["data_schema"].schema is not schema.schema
    assert form["data_schema"].schema == schema.schema
    markers = list(form["data_schema"].schema)
    assert len(markers) == 3
    assert markers[0] == "username"
    assert markers[0].description is None
    assert markers[1] == "password"
    assert markers[1].description is None
    assert markers[2] == "section_1"
    section_validator = form["data_schema"].schema["section_1"]
    assert isinstance(section_validator, data_entry_flow.section)
    # The section class is not replaced if there is no suggested value for the section
    assert section_validator is schema.schema["section_1"]
    # The section schema is not replaced if there is no suggested value for the section
    assert section_validator.schema is schema.schema["section_1"].schema
    section_markers = list(section_validator.schema.schema)
    assert len(section_markers) == 1
    assert section_markers[0] == "full_name"
    assert section_markers[0].description is None