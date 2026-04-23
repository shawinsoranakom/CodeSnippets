def test_root_path(self):
        async_request_factory = AsyncRequestFactory()
        request = async_request_factory.request(
            **{"path": "/root/somepath/", "root_path": "/root"}
        )
        self.assertEqual(request.path, "/root/somepath/")
        self.assertEqual(request.script_name, "/root")
        self.assertEqual(request.path_info, "/somepath/")