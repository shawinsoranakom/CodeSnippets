def test_postgres_ci_fields_deprecated(self):
        from django.contrib.postgres.fields import (
            ArrayField,
            CICharField,
            CIEmailField,
            CITextField,
        )

        class PostgresCIFieldsModel(models.Model):
            ci_char = CICharField(max_length=255)
            ci_email = CIEmailField()
            ci_text = CITextField()
            array_ci_text = ArrayField(CITextField())

        self.assertEqual(
            PostgresCIFieldsModel.check(),
            [
                checks.Error(
                    "django.contrib.postgres.fields.CICharField is removed except for "
                    "support in historical migrations.",
                    hint=(
                        'Use CharField(db_collation="…") with a case-insensitive '
                        "non-deterministic collation instead."
                    ),
                    obj=PostgresCIFieldsModel._meta.get_field("ci_char"),
                    id="fields.E905",
                ),
                checks.Error(
                    "django.contrib.postgres.fields.CIEmailField is removed except for "
                    "support in historical migrations.",
                    hint=(
                        'Use EmailField(db_collation="…") with a case-insensitive '
                        "non-deterministic collation instead."
                    ),
                    obj=PostgresCIFieldsModel._meta.get_field("ci_email"),
                    id="fields.E906",
                ),
                checks.Error(
                    "django.contrib.postgres.fields.CITextField is removed except for "
                    "support in historical migrations.",
                    hint=(
                        'Use TextField(db_collation="…") with a case-insensitive '
                        "non-deterministic collation instead."
                    ),
                    obj=PostgresCIFieldsModel._meta.get_field("ci_text"),
                    id="fields.E907",
                ),
                checks.Error(
                    "Base field for array has errors:\n"
                    "    django.contrib.postgres.fields.CITextField is removed except "
                    "for support in historical migrations. (fields.E907)",
                    obj=PostgresCIFieldsModel._meta.get_field("array_ci_text"),
                    id="postgres.E001",
                ),
            ],
        )