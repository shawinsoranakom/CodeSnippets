def test_getuser_raises_exception(self):
        # TODO: Drop ImportError and KeyError when dropping support for PY312.
        for exc in (ImportError, KeyError, OSError):
            with self.subTest(exc=str(exc)):
                with mock.patch("getpass.getuser", side_effect=exc):
                    self.assertEqual(management.get_system_username(), "")