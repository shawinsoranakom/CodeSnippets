def test_upload_file_default_values(self):
        self.assertEqual(200, config.get_option("server.maxUploadSize"))