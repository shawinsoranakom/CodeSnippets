def test_file_response_closing(self):
        """
        View returning a FileResponse properly closes the file and http
        response when file_wrapper is used.
        """
        env = RequestFactory().get("/fileresponse/").environ
        handler = FileWrapperHandler(BytesIO(), BytesIO(), BytesIO(), env)
        handler.run(get_internal_wsgi_application())
        # Sendfile is used only when file_wrapper has been used.
        self.assertTrue(handler._used_sendfile)
        # Fetch the original response object.
        self.assertIn("response", FILE_RESPONSE_HOLDER)
        response = FILE_RESPONSE_HOLDER["response"]
        # The response and file buffers are closed.
        self.assertIs(response.closed, True)
        buf1, buf2 = FILE_RESPONSE_HOLDER["buffers"]
        self.assertIs(buf1.closed, True)
        self.assertIs(buf2.closed, True)
        FILE_RESPONSE_HOLDER.clear()