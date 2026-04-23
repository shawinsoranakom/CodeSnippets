def assertGeneratedIntegerFieldIsInvalid(self, *, db_persist):
        class TestModel(Model):
            generated = models.GeneratedField(
                expression=models.Value(1),
                output_field=models.IntegerField(),
                db_persist=db_persist,
            )

        class TestModelAdmin(ModelAdmin):
            date_hierarchy = "generated"

        self.assertIsInvalid(
            TestModelAdmin,
            TestModel,
            "The value of 'date_hierarchy' must be a DateField or DateTimeField.",
            "admin.E128",
        )