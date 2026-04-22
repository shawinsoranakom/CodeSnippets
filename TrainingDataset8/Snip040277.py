def test_success_request(self):
        """Test request success when valid parameters are provided."""

        with mock.patch("streamlit.components.v1.components.os.path.isdir"):
            # We don't need the return value in this case.
            declare_component("test", path=PATH)

        with mock.patch(
            "streamlit.web.server.component_request_handler.open",
            mock.mock_open(read_data="Test Content"),
        ):
            response = self._request_component(
                "tests.streamlit.web.server.component_request_handler_test.test"
            )

        self.assertEqual(200, response.code)
        self.assertEqual(b"Test Content", response.body)