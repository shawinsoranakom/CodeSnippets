def test_no_collision_across_apps_interpolation(self, apps):
        constraint = models.CheckConstraint(
            condition=models.Q(id__gt=0), name="%(app_label)s_%(class)s_foo"
        )

        class Model1(models.Model):
            class Meta:
                app_label = "basic"
                constraints = [constraint]

        class Model2(models.Model):
            class Meta:
                app_label = "check_framework"
                constraints = [constraint]

        self.assertEqual(checks.run_checks(app_configs=apps.get_app_configs()), [])