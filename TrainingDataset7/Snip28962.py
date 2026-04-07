def test_not_associated_with_field_name(self):
        class TestModelAdmin(ModelAdmin):
            list_filter = (BooleanFieldListFilter,)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_filter[0]' must not inherit from 'FieldListFilter'.",
            "admin.E114",
        )