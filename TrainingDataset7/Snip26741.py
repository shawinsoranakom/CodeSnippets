def test_exception_in_render_passed_to_process_exception(self):
        response = self.client.get("/middleware_exceptions/exception_in_render/")
        self.assertEqual(response.content, b"Exception caught")