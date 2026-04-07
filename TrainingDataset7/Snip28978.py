def test_random_marker_not_alone(self):
        class TestModelAdmin(ModelAdmin):
            ordering = ("?", "name")

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'ordering' has the random ordering marker '?', but contains "
            "other fields as well.",
            "admin.E032",
            hint='Either remove the "?", or remove the other fields.',
        )