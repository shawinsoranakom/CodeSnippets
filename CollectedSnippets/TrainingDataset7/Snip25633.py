def test_db_set_default_no_db_default(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.DB_SET_DEFAULT)

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(databases=self.databases),
            [
                Error(
                    "Field specifies on_delete=DB_SET_DEFAULT, but has no db_default "
                    "value.",
                    hint="Set a db_default value, or change the on_delete rule.",
                    obj=field,
                    id="fields.E322",
                )
            ],
        )