def test_not_swapped_model(self):
        class SwappableModel(models.Model):
            # A model that can be, but isn't swapped out. References to this
            # model should *not* raise any validation error.
            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        class Model(models.Model):
            explicit_fk = models.ForeignKey(
                SwappableModel,
                models.CASCADE,
                related_name="explicit_fk",
            )
            implicit_fk = models.ForeignKey(
                "invalid_models_tests.SwappableModel",
                models.CASCADE,
                related_name="implicit_fk",
            )
            explicit_m2m = models.ManyToManyField(
                SwappableModel, related_name="explicit_m2m"
            )
            implicit_m2m = models.ManyToManyField(
                "invalid_models_tests.SwappableModel",
                related_name="implicit_m2m",
            )

        explicit_fk = Model._meta.get_field("explicit_fk")
        self.assertEqual(explicit_fk.check(), [])

        implicit_fk = Model._meta.get_field("implicit_fk")
        self.assertEqual(implicit_fk.check(), [])

        explicit_m2m = Model._meta.get_field("explicit_m2m")
        self.assertEqual(explicit_m2m.check(from_model=Model), [])

        implicit_m2m = Model._meta.get_field("implicit_m2m")
        self.assertEqual(implicit_m2m.check(from_model=Model), [])