def test_collision_across_apps(self, apps):
        index = models.Index(fields=["id"], name="foo")

        class Model1(models.Model):
            class Meta:
                app_label = "basic"
                indexes = [index]

        class Model2(models.Model):
            class Meta:
                app_label = "check_framework"
                indexes = [index]

        self.assertEqual(
            checks.run_checks(app_configs=apps.get_app_configs()),
            [
                Error(
                    "index name 'foo' is not unique among models: basic.Model1, "
                    "check_framework.Model2.",
                    id="models.E030",
                ),
            ],
        )