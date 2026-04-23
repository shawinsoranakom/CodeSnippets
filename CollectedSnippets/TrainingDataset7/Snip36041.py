def test_python_m_django(self):
        main = "/usr/lib/pythonX.Y/site-packages/django/__main__.py"
        argv = [main, "runserver"]
        mock_call = self.patch_autoreload(argv)
        with mock.patch("django.__main__.__file__", main):
            with mock.patch.dict(sys.modules, {"__main__": django.__main__}):
                autoreload.restart_with_reloader()
            self.assertEqual(mock_call.call_count, 1)
            self.assertEqual(
                mock_call.call_args[0][0],
                [self.executable, "-Wall", "-m", "django"] + argv[1:],
            )