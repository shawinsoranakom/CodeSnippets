def test_register_serializer_for_migrations(self):
        tests = (
            (DateRange(empty=True), DateRangeField),
            (DateTimeRange(empty=True), DateRangeField),
            (DateTimeTZRange(None, None, "[]"), DateTimeRangeField),
            (NumericRange(Decimal("1.0"), Decimal("5.0"), "()"), DecimalRangeField),
            (NumericRange(1, 10), IntegerRangeField),
        )

        def assertNotSerializable():
            for default, test_field in tests:
                with self.subTest(default=default):
                    field = test_field(default=default)
                    with self.assertRaisesMessage(
                        ValueError, "Cannot serialize: %s" % default.__class__.__name__
                    ):
                        MigrationWriter.serialize(field)

        assertNotSerializable()
        import_name = "psycopg.types.range" if is_psycopg3 else "psycopg2.extras"
        with self.modify_settings(INSTALLED_APPS={"append": "django.contrib.postgres"}):
            for default, test_field in tests:
                with self.subTest(default=default):
                    field = test_field(default=default)
                    serialized_field, imports = MigrationWriter.serialize(field)
                    self.assertEqual(
                        imports,
                        {
                            "import django.contrib.postgres.fields.ranges",
                            f"import {import_name}",
                        },
                    )
                    self.assertIn(
                        f"{field.__module__}.{field.__class__.__name__}"
                        f"(default={import_name}.{default!r})",
                        serialized_field,
                    )
        assertNotSerializable()