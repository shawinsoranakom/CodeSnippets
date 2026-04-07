def test_skips_newer_files_in_remote_storage(self):
        """
        collectstatic skips newer files in a remote storage.
        run_collectstatic() in setUp() copies the static files, then files are
        always skipped after NeverCopyRemoteStorage is activated since
        NeverCopyRemoteStorage.get_modified_time() returns a datetime in the
        future to simulate an unmodified file.
        """
        stdout = StringIO()
        self.run_collectstatic(stdout=stdout, verbosity=2)
        output = stdout.getvalue()
        self.assertIn("Skipping 'test.txt' (not modified)", output)