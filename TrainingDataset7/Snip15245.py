def test_inline_self_check(self):
        class TwoAlbumFKAndAnEInline(admin.TabularInline):
            model = TwoAlbumFKAndAnE

        class MyAdmin(admin.ModelAdmin):
            inlines = [TwoAlbumFKAndAnEInline]

        errors = MyAdmin(Album, AdminSite()).check()
        expected = [
            checks.Error(
                "'admin_checks.TwoAlbumFKAndAnE' has more than one ForeignKey "
                "to 'admin_checks.Album'. You must specify a 'fk_name' "
                "attribute.",
                obj=TwoAlbumFKAndAnEInline,
                id="admin.E202",
            )
        ]
        self.assertEqual(errors, expected)