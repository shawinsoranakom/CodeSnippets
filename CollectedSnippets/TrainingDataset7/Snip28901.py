def test_item_not_a_pair(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = ((),)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'fieldsets[0]' must be of length 2.",
            "admin.E009",
        )