def test_support_binary_files_request(self):
        """Test support for binary files reads."""

        def _open_read(m, payload):
            is_binary = False
            args, kwargs = m.call_args
            if len(args) > 1:
                if "b" in args[1]:
                    is_binary = True
            encoding = "utf-8"
            if "encoding" in kwargs:
                encoding = kwargs["encoding"]

            if is_binary:
                from io import BytesIO

                return BytesIO(payload)
            else:
                from io import TextIOWrapper

                return TextIOWrapper(str(payload, encoding=encoding))

        with mock.patch("streamlit.components.v1.components.os.path.isdir"):
            declare_component("test", path=PATH)

        payload = b"\x00\x01\x00\x00\x00\x0D\x00\x80"  # binary non utf-8 payload

        with mock.patch("streamlit.web.server.component_request_handler.open") as m:
            m.return_value.__enter__ = lambda _: _open_read(m, payload)
            response = self._request_component(
                "tests.streamlit.web.server.component_request_handler_test.test"
            )

        self.assertEqual(200, response.code)
        self.assertEqual(
            payload,
            response.body,
        )