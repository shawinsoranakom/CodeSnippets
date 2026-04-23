def test_manage_py(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "manage.py"
            script.touch()
            argv = [str(script), "runserver"]
            mock_call = self.patch_autoreload(argv)
            with mock.patch("__main__.__spec__", None):
                autoreload.restart_with_reloader()
            self.assertEqual(mock_call.call_count, 1)
            self.assertEqual(
                mock_call.call_args[0][0],
                [self.executable, "-Wall"] + argv,
            )