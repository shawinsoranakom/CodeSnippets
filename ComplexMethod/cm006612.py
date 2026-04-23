async def test_run_and_validate_update_outputs_with_multiple_outputs(self):
        """Test run_and_validate_update_outputs with multiple outputs."""

        class TestComponent(Component):
            def build(self) -> None:
                pass

            def get_output1(self) -> str:
                """Method that returns a string."""
                return "output1"

            def get_output2(self) -> str:
                """Method that returns a string."""
                return "output2"

            def update_outputs(self, frontend_node, field_name, field_value):  # noqa: ARG002
                if field_name == "add_output":
                    frontend_node["outputs"].extend(
                        [
                            {
                                "name": "output1",
                                "type": "str",
                                "display_name": "Output 1",
                                "method": "get_output1",
                            },
                            {
                                "name": "output2",
                                "type": "str",
                                "display_name": "Output 2",
                                "method": "get_output2",
                            },
                        ]
                    )
                return frontend_node

        component = TestComponent()
        frontend_node = {"outputs": []}

        # Test adding multiple outputs
        updated_node = await component.run_and_validate_update_outputs(
            frontend_node=frontend_node, field_name="add_output", field_value=True
        )

        assert len(updated_node["outputs"]) == 2
        assert updated_node["outputs"][0]["name"] == "output1"
        assert updated_node["outputs"][1]["name"] == "output2"
        for output in updated_node["outputs"]:
            assert "types" in output
            assert "selected" in output
            # The component adds only 'Text' type for string outputs
            assert set(output["types"]) == {"Text"}
            assert output["selected"] == "Text"