def test_register_component_no_path(self):
        """It's not an error to register a component without a path."""
        registry = ComponentRegistry.instance()

        # Return None when the component hasn't been registered
        self.assertIsNone(registry.get_component_path("test_component"))

        # And also return None when the component doesn't have a path
        registry.register_component(
            CustomComponent("test_component", url="http://not.a.url")
        )
        self.assertIsNone(registry.get_component_path("test_component"))