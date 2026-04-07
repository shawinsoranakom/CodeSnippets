def test_sys_paths_absolute(self):
        paths = list(autoreload.sys_path_directories())
        self.assertTrue(all(p.is_absolute() for p in paths))