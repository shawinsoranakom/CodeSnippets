def test_primary_key(self):
        class Model(models.Model):
            field = models.FileField(primary_key=False, upload_to="somewhere")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'primary_key' is not a valid argument for a FileField.",
                    obj=field,
                    id="fields.E201",
                )
            ],
        )