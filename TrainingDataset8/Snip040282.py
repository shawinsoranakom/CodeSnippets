def test_invalid_content_request(self):
        """Test request failure when invalid content (file) is provided."""

        with mock.patch("streamlit.components.v1.components.os.path.isdir"):
            declare_component("test", path=PATH)

        with mock.patch("streamlit.web.server.component_request_handler.open") as m:
            m.side_effect = OSError("Invalid content")
            response = self._request_component(
                "tests.streamlit.web.server.component_request_handler_test.test"
            )

        self.assertEqual(404, response.code)
        self.assertEqual(
            b"read error",
            response.body,
        )