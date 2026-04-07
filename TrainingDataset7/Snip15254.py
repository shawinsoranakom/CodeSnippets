def test_nonexistent_field_on_inline(self):
        class CityInline(admin.TabularInline):
            model = City
            readonly_fields = ["i_dont_exist"]  # Missing attribute

        errors = CityInline(State, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'readonly_fields[0]' refers to 'i_dont_exist', which is "
                "not a callable, an attribute of 'CityInline', or an attribute of "
                "'admin_checks.City'.",
                obj=CityInline,
                id="admin.E035",
            )
        ]
        self.assertEqual(errors, expected)