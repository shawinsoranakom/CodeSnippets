def test_collision_in_same_model(self):
        class Model(models.Model):
            class Meta:
                constraints = [
                    models.CheckConstraint(condition=models.Q(id__gt=0), name="foo"),
                    models.CheckConstraint(condition=models.Q(id__lt=100), name="foo"),
                ]

        self.assertEqual(
            checks.run_checks(app_configs=self.apps.get_app_configs()),
            [
                Error(
                    "constraint name 'foo' is not unique for model "
                    "check_framework.Model.",
                    id="models.E031",
                ),
            ],
        )