def test_watch_dir_with_unresolvable_path(self):
        path = Path("unresolvable_directory")
        with mock.patch.object(Path, "absolute", side_effect=FileNotFoundError):
            self.reloader.watch_dir(path, "**/*.mo")
        self.assertEqual(list(self.reloader.directory_globs), [])