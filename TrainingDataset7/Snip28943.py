def test_invalid_m2m_related_name(self):
        class TestModelAdmin(ModelAdmin):
            list_display = ["featured"]

        self.assertIsInvalid(
            TestModelAdmin,
            Band,
            "The value of 'list_display[0]' must not be a many-to-many field or a "
            "reverse foreign key.",
            "admin.E109",
        )