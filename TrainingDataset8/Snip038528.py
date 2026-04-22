def test_only_url(self):
        """Succeed when a URL is provided."""
        component = components.declare_component("test", url=URL)
        self.assertEqual(URL, component.url)
        self.assertIsNone(component.path)

        self.assertEqual(
            ComponentRegistry.instance().get_component_path("components_test"),
            component.abspath,
        )