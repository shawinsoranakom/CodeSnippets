def test_collision_in_same_app(self):
        class Model1(models.Model):
            class Meta:
                db_table = "test_table"

        class Model2(models.Model):
            class Meta:
                db_table = "test_table"

        self.assertEqual(
            checks.run_checks(app_configs=self.apps.get_app_configs()),
            [
                Error(
                    "db_table 'test_table' is used by multiple models: "
                    "check_framework.Model1, check_framework.Model2.",
                    obj="test_table",
                    id="models.E028",
                )
            ],
        )