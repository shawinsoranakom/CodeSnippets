def test_collect_static_files_permissions(self):
        call_command("collectstatic", **self.command_params)
        static_root = Path(settings.STATIC_ROOT)
        test_file = static_root / "test.txt"
        file_mode = test_file.stat().st_mode & 0o777
        self.assertEqual(file_mode, 0o655)
        tests = [
            static_root / "subdir",
            static_root / "nested",
            static_root / "nested" / "css",
        ]
        for directory in tests:
            with self.subTest(directory=directory):
                dir_mode = directory.stat().st_mode & 0o777
                self.assertEqual(dir_mode, 0o765)