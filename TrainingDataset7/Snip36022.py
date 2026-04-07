def test_sys_paths_non_existing(self):
        nonexistent_file = Path(self.directory.name) / "does_not_exist"
        with extend_sys_path(str(nonexistent_file)):
            paths = list(autoreload.sys_path_directories())
        self.assertNotIn(nonexistent_file, paths)
        self.assertNotIn(nonexistent_file.parent, paths)