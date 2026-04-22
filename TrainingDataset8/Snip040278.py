def test_outside_component_root_request(self):
        """Tests to ensure a path based on the root directory (and therefore
        outside of the component root) is disallowed."""

        with mock.patch("streamlit.components.v1.components.os.path.isdir"):
            # We don't need the return value in this case.
            declare_component("test", path=PATH)

        response = self._request_component(
            "tests.streamlit.web.server.component_request_handler_test.test//etc/hosts"
        )

        self.assertEqual(403, response.code)
        self.assertEqual(b"forbidden", response.body)