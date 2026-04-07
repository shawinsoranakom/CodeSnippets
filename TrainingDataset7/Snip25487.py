def test_forbidden_files_and_folders(self):
        class Model(models.Model):
            field = models.FilePathField(allow_files=False, allow_folders=False)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "FilePathFields must have either 'allow_files' or 'allow_folders' "
                    "set to True.",
                    obj=field,
                    id="fields.E140",
                ),
            ],
        )