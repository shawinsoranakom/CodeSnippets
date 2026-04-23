def assertGeneratedDateTimeFieldIsValid(self, *, db_persist):
        class TestModel(Model):
            date = models.DateTimeField()
            date_copy = models.GeneratedField(
                expression=F("date"),
                output_field=models.DateTimeField(),
                db_persist=db_persist,
            )

        class TestModelAdmin(ModelAdmin):
            date_hierarchy = "date_copy"

        self.assertIsValid(TestModelAdmin, TestModel)