def test_m2m_field_table_name_clash(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foos = models.ManyToManyField(Foo, db_table="clash")

        class Baz(models.Model):
            foos = models.ManyToManyField(Foo, db_table="clash")

        self.assertEqual(
            Bar.check() + Baz.check(),
            [
                Error(
                    "The field's intermediary table 'clash' clashes with the "
                    "table name of 'invalid_models_tests.Baz.foos'.",
                    obj=Bar._meta.get_field("foos"),
                    id="fields.E340",
                ),
                Error(
                    "The field's intermediary table 'clash' clashes with the "
                    "table name of 'invalid_models_tests.Bar.foos'.",
                    obj=Baz._meta.get_field("foos"),
                    id="fields.E340",
                ),
            ],
        )