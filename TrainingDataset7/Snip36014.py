def test_entrypoint_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "django-admin-script.py"
            script_path.touch()
            with mock.patch(
                "sys.argv", [script_path.with_name("django-admin"), "runserver"]
            ):
                self.assertEqual(
                    autoreload.get_child_arguments(),
                    [sys.executable, script_path, "runserver"],
                )