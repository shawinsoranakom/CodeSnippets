def test_symlink_outside_component_root_request(self):
        """Tests to ensure a path symlinked to a file outside the component
        root directory is disallowed."""

        with mock.patch("streamlit.components.v1.components.os.path.isdir"):
            # We don't need the return value in this case.
            declare_component("test", path=PATH)

        with mock.patch(
            "streamlit.web.server.component_request_handler.os.path.realpath",
            side_effect=[PATH, "/etc/hosts"],
        ):
            response = self._request_component(
                "tests.streamlit.web.server.component_request_handler_test.test"
            )

        self.assertEqual(403, response.code)
        self.assertEqual(b"forbidden", response.body)