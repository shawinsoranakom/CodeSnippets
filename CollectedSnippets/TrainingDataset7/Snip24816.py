def test_content_type_mutually_exclusive(self):
        msg = (
            "'headers' must not contain 'Content-Type' when the "
            "'content_type' parameter is provided."
        )
        with self.assertRaisesMessage(ValueError, msg):
            HttpResponse(
                "hello",
                content_type="application/json",
                headers={"Content-Type": "text/csv"},
            )