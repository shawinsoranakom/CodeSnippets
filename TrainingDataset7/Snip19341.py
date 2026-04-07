def test_collision_across_apps_database_routers_installed(self, apps):
        class Model1(models.Model):
            class Meta:
                app_label = "basic"
                db_table = "test_table"

        class Model2(models.Model):
            class Meta:
                app_label = "check_framework"
                db_table = "test_table"

        self.assertEqual(
            checks.run_checks(app_configs=apps.get_app_configs()),
            [
                Warning(
                    "db_table 'test_table' is used by multiple models: "
                    "basic.Model1, check_framework.Model2.",
                    hint=(
                        "You have configured settings.DATABASE_ROUTERS. Verify "
                        "that basic.Model1, check_framework.Model2 are correctly "
                        "routed to separate databases."
                    ),
                    obj="test_table",
                    id="models.W035",
                )
            ],
        )