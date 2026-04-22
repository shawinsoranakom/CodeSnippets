def test_register_invalid_path(self):
        """We raise an exception if a component is registered with a
        non-existent path.
        """
        test_path = "/a/test/component/directory"

        registry = ComponentRegistry.instance()
        with self.assertRaises(StreamlitAPIException) as ctx:
            registry.register_component(CustomComponent("test_component", test_path))
        self.assertIn("No such component directory", str(ctx.exception))