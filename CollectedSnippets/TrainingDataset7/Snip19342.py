def test_no_collision_for_unmanaged_models(self):
        class Unmanaged(models.Model):
            class Meta:
                db_table = "test_table"
                managed = False

        class Managed(models.Model):
            class Meta:
                db_table = "test_table"

        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [])