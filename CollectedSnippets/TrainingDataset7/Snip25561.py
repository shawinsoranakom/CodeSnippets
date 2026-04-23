def test_on_delete_set_default_without_default_value(self):
        class Person(models.Model):
            pass

        class Model(models.Model):
            foreign_key = models.ForeignKey("Person", models.SET_DEFAULT)

        field = Model._meta.get_field("foreign_key")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field specifies on_delete=SET_DEFAULT, but has no default value.",
                    hint="Set a default value, or change the on_delete rule.",
                    obj=field,
                    id="fields.E321",
                ),
            ],
        )