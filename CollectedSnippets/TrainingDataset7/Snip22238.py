def test_relative_path(self, path=["fixtures", "absolute.json"]):
        relative_path = os.path.join(*path)
        cwd = os.getcwd()
        try:
            os.chdir(_cur_dir)
            management.call_command(
                "loaddata",
                relative_path,
                verbosity=0,
            )
        finally:
            os.chdir(cwd)
        self.assertEqual(Absolute.objects.count(), 1)