def test_file_change_after_collectstatic(self):
        # Create initial static files.
        file_contents = (
            ("foo.png", "foo"),
            ("bar.css", 'url("foo.png")\nurl("xyz.png")'),
            ("xyz.png", "xyz"),
        )
        for filename, content in file_contents:
            with open(self._get_filename_path(filename), "w") as f:
                f.write(content)

        with self.modify_settings(STATICFILES_DIRS={"append": self._temp_dir}):
            finders.get_finder.cache_clear()
            err = StringIO()
            # First collectstatic run.
            call_command("collectstatic", interactive=False, verbosity=0, stderr=err)
            relpath = self.hashed_file_path("test/bar.css")
            with storage.staticfiles_storage.open(relpath) as relfile:
                content = relfile.read()
                self.assertIn(b"foo.acbd18db4cc2.png", content)
                self.assertIn(b"xyz.d16fb36f0911.png", content)

            # Change the contents of the png files.
            for filename in ("foo.png", "xyz.png"):
                with open(self._get_filename_path(filename), "w+b") as f:
                    f.write(b"new content of file to change its hash")

            # The hashes of the png files in the CSS file are updated after
            # a second collectstatic.
            call_command("collectstatic", interactive=False, verbosity=0, stderr=err)
            relpath = self.hashed_file_path("test/bar.css")
            with storage.staticfiles_storage.open(relpath) as relfile:
                content = relfile.read()
                self.assertIn(b"foo.57a5cb9ba68d.png", content)
                self.assertIn(b"xyz.57a5cb9ba68d.png", content)