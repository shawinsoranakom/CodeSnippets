def test_register_component_with_path(self):
        """Registering a component should associate it with its path."""
        test_path = "/a/test/component/directory"

        def isdir(path):
            return path == test_path

        registry = ComponentRegistry.instance()
        with mock.patch(
            "streamlit.components.v1.components.os.path.isdir", side_effect=isdir
        ):
            registry.register_component(
                CustomComponent("test_component", path=test_path)
            )

        self.assertEqual(test_path, registry.get_component_path("test_component"))