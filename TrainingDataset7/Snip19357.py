def test_user_specified_details(self):
        class MyField(models.Field):
            system_check_deprecated_details = {
                "msg": "This field is deprecated and will be removed soon.",
                "hint": "Use something else.",
                "id": "fields.W999",
            }

        class Model(models.Model):
            name = MyField()

        model = Model()
        self.assertEqual(
            model.check(),
            [
                checks.Warning(
                    msg="This field is deprecated and will be removed soon.",
                    hint="Use something else.",
                    obj=Model._meta.get_field("name"),
                    id="fields.W999",
                )
            ],
        )