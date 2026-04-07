def test_on_delete_set_null_on_non_nullable_field(self):
        class Person(models.Model):
            pass

        class Model(models.Model):
            foreign_key = models.ForeignKey("Person", models.SET_NULL)

        field = Model._meta.get_field("foreign_key")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field specifies on_delete=SET_NULL, but cannot be null.",
                    hint=(
                        "Set null=True argument on the field, or change the on_delete "
                        "rule."
                    ),
                    obj=field,
                    id="fields.E320",
                ),
            ],
        )