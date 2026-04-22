def test_only_path(self):
        """Succeed when a path is provided."""

        def isdir(path):
            return path == PATH or path == os.path.abspath(PATH)

        with mock.patch(
            "streamlit.components.v1.components.os.path.isdir", side_effect=isdir
        ):
            component = components.declare_component("test", path=PATH)

        self.assertEqual(PATH, component.path)
        self.assertIsNone(component.url)

        self.assertEqual(
            ComponentRegistry.instance().get_component_path(component.name),
            component.abspath,
        )