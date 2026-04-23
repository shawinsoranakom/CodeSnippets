def test_django_admin_py(self):
        "django_admin.py will autocomplete option flags"
        self._user_input("django-admin sqlmigrate --verb")
        output = self._run_autocomplete()
        self.assertEqual(output, ["--verbosity="])