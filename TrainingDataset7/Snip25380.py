def test_m2m_field_table_name_clash_database_routers_installed(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foos = models.ManyToManyField(Foo, db_table="clash")

        class Baz(models.Model):
            foos = models.ManyToManyField(Foo, db_table="clash")

        self.assertEqual(
            Bar.check() + Baz.check(),
            [
                Warning(
                    "The field's intermediary table 'clash' clashes with the "
                    "table name of 'invalid_models_tests.%s.foos'." % clashing_model,
                    obj=model_cls._meta.get_field("foos"),
                    hint=(
                        "You have configured settings.DATABASE_ROUTERS. Verify "
                        "that the table of 'invalid_models_tests.%s.foos' is "
                        "correctly routed to a separate database." % clashing_model
                    ),
                    id="fields.W344",
                )
                for model_cls, clashing_model in [(Bar, "Baz"), (Baz, "Bar")]
            ],
        )