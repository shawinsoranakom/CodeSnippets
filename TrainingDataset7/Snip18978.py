def test_file_response_call_request_finished(self):
        env = RequestFactory().get("/fileresponse/").environ
        handler = FileWrapperHandler(BytesIO(), BytesIO(), BytesIO(), env)
        with mock.MagicMock() as signal_handler:
            request_finished.connect(signal_handler)
            handler.run(get_internal_wsgi_application())
            self.assertEqual(signal_handler.call_count, 1)