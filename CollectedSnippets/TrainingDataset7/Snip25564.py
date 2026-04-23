def test_referencing_to_swapped_model(self):
        class Replacement(models.Model):
            pass

        class SwappedModel(models.Model):
            class Meta:
                swappable = "TEST_SWAPPED_MODEL"

        class Model(models.Model):
            explicit_fk = models.ForeignKey(
                SwappedModel,
                models.CASCADE,
                related_name="explicit_fk",
            )
            implicit_fk = models.ForeignKey(
                "invalid_models_tests.SwappedModel",
                models.CASCADE,
                related_name="implicit_fk",
            )
            explicit_m2m = models.ManyToManyField(
                SwappedModel, related_name="explicit_m2m"
            )
            implicit_m2m = models.ManyToManyField(
                "invalid_models_tests.SwappedModel",
                related_name="implicit_m2m",
            )

        fields = [
            Model._meta.get_field("explicit_fk"),
            Model._meta.get_field("implicit_fk"),
            Model._meta.get_field("explicit_m2m"),
            Model._meta.get_field("implicit_m2m"),
        ]

        expected_error = Error(
            (
                "Field defines a relation with the model "
                "'invalid_models_tests.SwappedModel', which has been swapped out."
            ),
            hint="Update the relation to point at 'settings.TEST_SWAPPED_MODEL'.",
            id="fields.E301",
        )

        for field in fields:
            expected_error.obj = field
            self.assertEqual(field.check(from_model=Model), [expected_error])