def test_no_collision_abstract_model_interpolation(self):
        class AbstractModel(models.Model):
            class Meta:
                constraints = [
                    models.CheckConstraint(
                        condition=models.Q(id__gt=0), name="%(app_label)s_%(class)s_foo"
                    ),
                ]
                abstract = True

        class Model1(AbstractModel):
            pass

        class Model2(AbstractModel):
            pass

        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [])