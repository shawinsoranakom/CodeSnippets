def test_manage_py(self):
        "manage.py will autocomplete option flags"
        self._user_input("manage.py sqlmigrate --verb")
        output = self._run_autocomplete()
        self.assertEqual(output, ["--verbosity="])