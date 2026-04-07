def test_pathological_http_method(self):
        """
        The edge case of an HTTP request that spoofs an existing method name is
        caught.
        """
        self.assertEqual(
            SimpleView.as_view()(
                self.rf.get("/", REQUEST_METHOD="DISPATCH")
            ).status_code,
            405,
        )