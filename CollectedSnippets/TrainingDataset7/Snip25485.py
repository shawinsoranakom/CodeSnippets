def test_upload_to_starts_with_slash(self):
        class Model(models.Model):
            field = models.FileField(upload_to="/somewhere")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "FileField's 'upload_to' argument must be a relative path, not "
                    "an absolute path.",
                    obj=field,
                    id="fields.E202",
                    hint="Remove the leading slash.",
                )
            ],
        )