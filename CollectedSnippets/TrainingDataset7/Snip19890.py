def test_pointing_to_swapped_model(self):
        class Replacement(models.Model):
            pass

        class SwappedModel(models.Model):
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey()

            class Meta:
                swappable = "TEST_SWAPPED_MODEL"

        class Model(models.Model):
            rel = GenericRelation("SwappedModel")

        self.assertEqual(
            Model.rel.field.check(),
            [
                checks.Error(
                    "Field defines a relation with the model "
                    "'contenttypes_tests.SwappedModel', "
                    "which has been swapped out.",
                    hint=(
                        "Update the relation to point at 'settings.TEST_SWAPPED_MODEL'."
                    ),
                    obj=Model.rel.field,
                    id="fields.E301",
                )
            ],
        )