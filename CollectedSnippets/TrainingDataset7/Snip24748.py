def test_root_path_prefix_boundary(self):
        async_request_factory = AsyncRequestFactory()
        # When path shares a textual prefix with root_path but not at a
        # segment boundary, path_info should be the full path.
        request = async_request_factory.request(
            **{"path": "/rootprefix/somepath/", "root_path": "/root"}
        )
        self.assertEqual(request.path, "/rootprefix/somepath/")
        self.assertEqual(request.script_name, "/root")
        self.assertEqual(request.path_info, "/rootprefix/somepath/")