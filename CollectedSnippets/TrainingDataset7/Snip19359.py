def test_user_specified_details(self):
        class MyField(models.Field):
            system_check_removed_details = {
                "msg": "Support for this field is gone.",
                "hint": "Use something else.",
                "id": "fields.E999",
            }

        class Model(models.Model):
            name = MyField()

        model = Model()
        self.assertEqual(
            model.check(),
            [
                checks.Error(
                    msg="Support for this field is gone.",
                    hint="Use something else.",
                    obj=Model._meta.get_field("name"),
                    id="fields.E999",
                )
            ],
        )