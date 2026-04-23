def test_invalid_reverse_related_field(self):
        class TestModelAdmin(ModelAdmin):
            list_display = ["song_set"]

        self.assertIsInvalid(
            TestModelAdmin,
            Band,
            "The value of 'list_display[0]' must not be a many-to-many field or a "
            "reverse foreign key.",
            "admin.E109",
        )