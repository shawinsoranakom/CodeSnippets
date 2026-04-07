def test_references_model_mixin(self):
        migrations.CreateModel(
            "name",
            fields=[],
            bases=(Mixin, models.Model),
        ).references_model("other_model", "migrations")