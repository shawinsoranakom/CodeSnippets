def test_ending_with_underscore(self):
        class Model(models.Model):
            field_ = models.CharField(max_length=10)
            m2m_ = models.ManyToManyField("self")

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Field names must not end with an underscore.",
                    obj=Model._meta.get_field("field_"),
                    id="fields.E001",
                ),
                Error(
                    "Field names must not end with an underscore.",
                    obj=Model._meta.get_field("m2m_"),
                    id="fields.E001",
                ),
            ],
        )