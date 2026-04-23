def test_file_wrapper_no_sendfile(self):
        env = {"SERVER_PROTOCOL": "HTTP/1.0"}
        handler = FileWrapperHandler(BytesIO(), BytesIO(), BytesIO(), env)
        handler.run(wsgi_app)
        self.assertFalse(handler._used_sendfile)
        self.assertEqual(handler.stdout.getvalue().splitlines()[-1], b"Hello World!")
        self.assertEqual(handler.stderr.getvalue(), b"")