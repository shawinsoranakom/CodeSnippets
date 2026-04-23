def test_environ_path_info_type(self):
        environ = self.request_factory.get("/%E2%A8%87%87%A5%E2%A8%A0").environ
        self.assertIsInstance(environ["PATH_INFO"], str)