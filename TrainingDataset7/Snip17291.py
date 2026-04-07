def test_relabeling(self):
        self.assertEqual(apps.get_app_config("relabeled").name, "apps")