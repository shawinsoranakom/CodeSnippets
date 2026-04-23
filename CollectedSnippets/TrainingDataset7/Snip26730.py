def test_process_view_return_none(self):
        response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(mw.log, ["processed view normal_view"])
        self.assertEqual(response.content, b"OK")