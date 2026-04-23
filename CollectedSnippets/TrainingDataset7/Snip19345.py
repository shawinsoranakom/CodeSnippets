def test_collision_in_different_models(self):
        index = models.Index(fields=["id"], name="foo")

        class Model1(models.Model):
            class Meta:
                indexes = [index]

        class Model2(models.Model):
            class Meta:
                indexes = [index]

        self.assertEqual(
            checks.run_checks(app_configs=self.apps.get_app_configs()),
            [
                Error(
                    "index name 'foo' is not unique among models: "
                    "check_framework.Model1, check_framework.Model2.",
                    id="models.E030",
                ),
            ],
        )