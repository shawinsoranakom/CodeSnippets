def test_collision_across_apps(self, apps):
        constraint = models.CheckConstraint(condition=models.Q(id__gt=0), name="foo")

        class Model1(models.Model):
            class Meta:
                app_label = "basic"
                constraints = [constraint]

        class Model2(models.Model):
            class Meta:
                app_label = "check_framework"
                constraints = [constraint]

        self.assertEqual(
            checks.run_checks(app_configs=apps.get_app_configs()),
            [
                Error(
                    "constraint name 'foo' is not unique among models: "
                    "basic.Model1, check_framework.Model2.",
                    id="models.E032",
                ),
            ],
        )