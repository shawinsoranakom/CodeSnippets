def test_check_sublists_for_duplicates(self):
        class MyModelAdmin(admin.ModelAdmin):
            fields = ["state", ["state"]]

        errors = MyModelAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'fields' contains duplicate field(s).",
                hint="Remove duplicates of 'state'.",
                obj=MyModelAdmin,
                id="admin.E006",
            )
        ]
        self.assertEqual(errors, expected)