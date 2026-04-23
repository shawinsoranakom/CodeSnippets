def test_foreign_key_to_abstract_model(self):
        class AbstractModel(models.Model):
            class Meta:
                abstract = True

        class Model(models.Model):
            rel_string_foreign_key = models.ForeignKey("AbstractModel", models.CASCADE)
            rel_class_foreign_key = models.ForeignKey(AbstractModel, models.CASCADE)

        fields = [
            Model._meta.get_field("rel_string_foreign_key"),
            Model._meta.get_field("rel_class_foreign_key"),
        ]
        expected_error = Error(
            "Field defines a relation with model 'AbstractModel', "
            "which is either not installed, or is abstract.",
            id="fields.E300",
        )
        for field in fields:
            expected_error.obj = field
            self.assertEqual(field.check(), [expected_error])