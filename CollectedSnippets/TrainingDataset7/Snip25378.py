def test_m2m_table_name_clash_database_routers_installed(self):
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
                Warning(
                    "The field's intermediary table 'myapp_bar' clashes with the "
                    "table name of 'invalid_models_tests.Bar'.",
                    obj=Foo._meta.get_field("bar"),
                    hint=(
                        "You have configured settings.DATABASE_ROUTERS. Verify "
                        "that the table of 'invalid_models_tests.Bar' is "
                        "correctly routed to a separate database."
                    ),
                    id="fields.W344",
                ),
            ],
        )