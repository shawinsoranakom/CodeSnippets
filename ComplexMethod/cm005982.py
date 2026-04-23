async def test_watsonx_fields_hidden_by_default(self, component_class, default_kwargs):
        """Test that WatsonX fields are hidden by default."""
        component = await self.component_setup(component_class, default_kwargs)

        # Find the WatsonX input fields
        watsonx_url_input = next(
            (inp for inp in component.inputs if hasattr(inp, "name") and inp.name == "base_url_ibm_watsonx"), None
        )
        project_id_input = next(
            (inp for inp in component.inputs if hasattr(inp, "name") and inp.name == "project_id"), None
        )

        assert watsonx_url_input is not None
        assert project_id_input is not None
        assert watsonx_url_input.show is False
        assert project_id_input.show is False