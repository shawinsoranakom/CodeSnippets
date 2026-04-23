def test_no_collision_across_apps_interpolation(self, apps):
        index = models.Index(fields=["id"], name="%(app_label)s_%(class)s_foo")

        class Model1(models.Model):
            class Meta:
                app_label = "basic"
                constraints = [index]

        class Model2(models.Model):
            class Meta:
                app_label = "check_framework"
                constraints = [index]

        self.assertEqual(checks.run_checks(app_configs=apps.get_app_configs()), [])