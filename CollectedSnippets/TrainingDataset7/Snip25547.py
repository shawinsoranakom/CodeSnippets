def test_m2m_to_abstract_model(self):
        class AbstractModel(models.Model):
            class Meta:
                abstract = True

        class Model(models.Model):
            rel_string_m2m = models.ManyToManyField("AbstractModel")
            rel_class_m2m = models.ManyToManyField(AbstractModel)

        fields = [
            Model._meta.get_field("rel_string_m2m"),
            Model._meta.get_field("rel_class_m2m"),
        ]
        expected_error = Error(
            "Field defines a relation with model 'AbstractModel', "
            "which is either not installed, or is abstract.",
            id="fields.E300",
        )
        for field in fields:
            expected_error.obj = field
            self.assertEqual(field.check(from_model=Model), [expected_error])