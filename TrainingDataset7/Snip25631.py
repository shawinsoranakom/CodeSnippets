def test_db_set_default_support(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            parent = models.ForeignKey(
                Parent, models.DB_SET_DEFAULT, db_default=models.Value(1)
            )

        field = Child._meta.get_field("parent")
        expected = (
            []
            if connection.features.supports_on_delete_db_default
            else [
                Error(
                    f"{connection.display_name} does not support a DB_SET_DEFAULT.",
                    hint="Change the on_delete rule to SET_DEFAULT.",
                    obj=field,
                    id="fields.E324",
                )
            ]
        )
        self.assertEqual(field.check(databases=self.databases), expected)