def test_real_apps_non_set(self):
        with self.assertRaises(AssertionError):
            ProjectState(real_apps=["contenttypes"])