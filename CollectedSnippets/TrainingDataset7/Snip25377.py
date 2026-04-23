def test_m2m_table_name_clash(self):
        class Foo(models.Model):
            bar = models.ManyToManyField("Bar", db_table="myapp_bar")

            class Meta:
                db_table = "myapp_foo"

        class Bar(models.Model):
            class Meta:
                db_table = "myapp_bar"

        self.assertEqual(
            Foo.check(),
            [
                Error(
                    "The field's intermediary table 'myapp_bar' clashes with the "
                    "table name of 'invalid_models_tests.Bar'.",
                    obj=Foo._meta.get_field("bar"),
                    id="fields.E340",
                )
            ],
        )