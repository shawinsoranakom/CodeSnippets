def test_register_duplicate_path(self):
        """It's not an error to re-register a component.
        (This can happen during development).
        """
        test_path_1 = "/a/test/component/directory"
        test_path_2 = "/another/test/component/directory"

        def isdir(path):
            return path in (test_path_1, test_path_2)

        registry = ComponentRegistry.instance()
        with mock.patch(
            "streamlit.components.v1.components.os.path.isdir", side_effect=isdir
        ):
            registry.register_component(CustomComponent("test_component", test_path_1))
            registry.register_component(CustomComponent("test_component", test_path_1))
            self.assertEqual(test_path_1, registry.get_component_path("test_component"))

            registry.register_component(CustomComponent("test_component", test_path_2))
            self.assertEqual(test_path_2, registry.get_component_path("test_component"))