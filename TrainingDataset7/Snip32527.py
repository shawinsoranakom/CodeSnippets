def test_protocol_relative_url_ignored(self):
        with override_settings(
            STATICFILES_DIRS=[os.path.join(TEST_ROOT, "project", "static_url_slash")],
            STATICFILES_FINDERS=["django.contrib.staticfiles.finders.FileSystemFinder"],
        ):
            self.run_collectstatic()
        relpath = self.hashed_file_path("ignored.css")
        self.assertEqual(relpath, "ignored.61707f5f4942.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertIn(b"//foobar", content)