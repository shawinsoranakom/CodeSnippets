def test_app_label_in_admin_checks(self):
        class RawIdNonexistentAdmin(admin.ModelAdmin):
            raw_id_fields = ("nonexistent",)

        errors = RawIdNonexistentAdmin(Album, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'raw_id_fields[0]' refers to 'nonexistent', "
                "which is not a field of 'admin_checks.Album'.",
                obj=RawIdNonexistentAdmin,
                id="admin.E002",
            )
        ]
        self.assertEqual(errors, expected)