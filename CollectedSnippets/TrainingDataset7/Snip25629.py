def test_db_cascade_support(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.DB_CASCADE)

        field = Child._meta.get_field("parent")
        expected = (
            []
            if connection.features.supports_on_delete_db_cascade
            else [
                Error(
                    f"{connection.display_name} does not support a DB_CASCADE.",
                    hint="Change the on_delete rule to CASCADE.",
                    obj=field,
                    id="fields.E324",
                )
            ]
        )
        self.assertEqual(field.check(databases=self.databases), expected)