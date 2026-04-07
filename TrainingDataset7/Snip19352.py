def test_collision_abstract_model(self):
        class AbstractModel(models.Model):
            class Meta:
                constraints = [
                    models.CheckConstraint(condition=models.Q(id__gt=0), name="foo")
                ]
                abstract = True

        class Model1(AbstractModel):
            pass

        class Model2(AbstractModel):
            pass

        self.assertEqual(
            checks.run_checks(app_configs=self.apps.get_app_configs()),
            [
                Error(
                    "constraint name 'foo' is not unique among models: "
                    "check_framework.Model1, check_framework.Model2.",
                    id="models.E032",
                ),
            ],
        )