def test_process_view_return_response(self):
        response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(response.content, b"Processed view normal_view")