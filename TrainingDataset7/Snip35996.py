def test_paths_are_pathlib_instances(self):
        for filename in autoreload.iter_all_python_module_files():
            self.assertIsInstance(filename, Path)