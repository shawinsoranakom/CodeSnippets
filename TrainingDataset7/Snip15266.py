def test_check_fieldset_sublists_for_duplicates(self):
        class MyModelAdmin(admin.ModelAdmin):
            fieldsets = [
                (None, {"fields": ["title", "album", ("title", "album")]}),
            ]

        errors = MyModelAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "There are duplicate field(s) in 'fieldsets[0][1]'.",
                hint="Remove duplicates of 'title', 'album'.",
                obj=MyModelAdmin,
                id="admin.E012",
            )
        ]
        self.assertEqual(errors, expected)