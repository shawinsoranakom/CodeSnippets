def test_force_script_name(self):
        async_request_factory = AsyncRequestFactory()
        request = async_request_factory.request(**{"path": "/FORCED_PREFIX/somepath/"})
        self.assertEqual(request.path, "/FORCED_PREFIX/somepath/")
        self.assertEqual(request.script_name, "/FORCED_PREFIX")
        self.assertEqual(request.path_info, "/somepath/")