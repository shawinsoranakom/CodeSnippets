def test_handle_path_notimplemented(self):
        self.run_collectstatic()
        self.assertFileNotFound("cleared.txt")