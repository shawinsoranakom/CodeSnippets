def test_not_callable(self):
        class TestModelAdmin(ModelAdmin):
            list_filter = [[42, 42]]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_filter[0][1]' must inherit from 'FieldListFilter'.",
            "admin.E115",
        )