def test_downloadable_file(self, file_name, content_disposition_header) -> None:
        """Downloadable files get an additional 'Content-Disposition' header
        that includes their user-specified filename.
        """
        # Add a downloadable file with a filename
        url = self.media_file_manager.add(
            b"mock_data",
            "video/mp4",
            "mock_coords",
            file_name=file_name,
            is_for_static_download=True,
        )
        rsp = self.fetch(url, method="GET")

        self.assertEqual(200, rsp.code)
        self.assertEqual(b"mock_data", rsp.body)
        self.assertEqual("video/mp4", rsp.headers["Content-Type"])
        self.assertEqual(str(len(b"mock_data")), rsp.headers["Content-Length"])
        self.assertEqual(content_disposition_header, rsp.headers["Content-Disposition"])