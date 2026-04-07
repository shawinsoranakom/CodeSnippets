def test_check_multiple_duplicates_across_fieldsets(self):
        class MyModelAdmin(admin.ModelAdmin):
            fieldsets = [
                ("Header 1", {"fields": ["title", "album"]}),
                ("Header 2", {"fields": ["album", "name"]}),
                ("Header 3", {"fields": ["name", "other", "title"]}),
            ]

        errors = MyModelAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "There are duplicate field(s) in 'fieldsets[1][1]'.",
                hint="Remove duplicates of 'album'.",
                obj=MyModelAdmin,
                id="admin.E012",
            ),
            checks.Error(
                "There are duplicate field(s) in 'fieldsets[2][1]'.",
                hint="Remove duplicates of 'title', 'name'.",
                obj=MyModelAdmin,
                id="admin.E012",
            ),
        ]
        self.assertEqual(errors, expected)