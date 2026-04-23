def test_postgres_jsonfield_deprecated(self):
        from django.contrib.postgres.fields import JSONField

        class PostgresJSONFieldModel(models.Model):
            field = JSONField()

        self.assertEqual(
            PostgresJSONFieldModel.check(),
            [
                checks.Error(
                    "django.contrib.postgres.fields.JSONField is removed except "
                    "for support in historical migrations.",
                    hint="Use django.db.models.JSONField instead.",
                    obj=PostgresJSONFieldModel._meta.get_field("field"),
                    id="fields.E904",
                ),
            ],
        )