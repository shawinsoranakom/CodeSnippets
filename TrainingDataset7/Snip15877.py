def test_honor_umask(self):
        _, err = self.run_django_admin(["startproject", "testproject"], umask=0o077)
        self.assertNoOutput(err)
        testproject_dir = os.path.join(self.test_dir, "testproject")
        self.assertIs(os.path.isdir(testproject_dir), True)
        tests = [
            (["manage.py"], 0o700),
            (["testproject"], 0o700),
            (["testproject", "settings.py"], 0o600),
        ]
        for paths, expected_mode in tests:
            file_path = os.path.join(testproject_dir, *paths)
            with self.subTest(paths[-1]):
                self.assertEqual(
                    stat.S_IMODE(os.stat(file_path).st_mode),
                    expected_mode,
                )