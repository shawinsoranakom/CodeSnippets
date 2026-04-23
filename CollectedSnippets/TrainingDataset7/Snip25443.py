def test_primary_key(self):
        # primary_key must be True. Refs #12467.
        class Model(models.Model):
            field = models.AutoField(primary_key=False)

            # Prevent Django from autocreating `id` AutoField, which would
            # result in an error, because a model must have exactly one
            # AutoField.
            another = models.IntegerField(primary_key=True)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "AutoFields must set primary_key=True.",
                    obj=field,
                    id="fields.E100",
                ),
            ],
        )