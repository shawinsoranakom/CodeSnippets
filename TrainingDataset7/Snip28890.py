def test_not_iterable(self):
        class TestModelAdmin(ModelAdmin):
            raw_id_fields = 10

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'raw_id_fields' must be a list or tuple.",
            "admin.E001",
        )