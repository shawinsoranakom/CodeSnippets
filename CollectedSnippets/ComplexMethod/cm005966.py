async def test_decomposition_strategy_field(self, component_class, default_kwargs):
        """Test that decomposition_strategy field is properly configured.

        This test verifies that the decomposition_strategy field has the correct
        options, default value, and advanced configuration.
        """
        component = await self.component_setup(component_class, default_kwargs)

        # Find the decomposition_strategy input
        decomposition_input = None
        for inp in component.inputs:
            if hasattr(inp, "name") and inp.name == "decomposition_strategy":
                decomposition_input = inp
                break

        assert decomposition_input is not None, "decomposition_strategy input not found"
        assert decomposition_input.display_name == "Decomposition Strategy"
        assert decomposition_input.value == "flexible"
        assert decomposition_input.options == ["flexible", "exact"]
        assert decomposition_input.advanced is True

        # Test setting different values
        component.decomposition_strategy = "exact"
        assert component.decomposition_strategy == "exact"

        component.decomposition_strategy = "flexible"
        assert component.decomposition_strategy == "flexible"