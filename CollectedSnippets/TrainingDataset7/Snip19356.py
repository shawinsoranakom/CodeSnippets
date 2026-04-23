def test_default_details(self):
        class MyField(models.Field):
            system_check_deprecated_details = {}

        class Model(models.Model):
            name = MyField()

        model = Model()
        self.assertEqual(
            model.check(),
            [
                checks.Warning(
                    msg="MyField has been deprecated.",
                    obj=Model._meta.get_field("name"),
                    id="fields.WXXX",
                )
            ],
        )