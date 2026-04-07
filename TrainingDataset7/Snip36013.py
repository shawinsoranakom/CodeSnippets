def test_use_exe_when_main_spec(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = Path(tmpdir) / "django-admin.exe"
            exe_path.touch()
            with mock.patch("sys.argv", [exe_path.with_suffix(""), "runserver"]):
                self.assertEqual(
                    autoreload.get_child_arguments(), [exe_path, "runserver"]
                )