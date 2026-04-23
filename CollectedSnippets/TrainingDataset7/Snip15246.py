def test_inline_with_specified(self):
        class TwoAlbumFKAndAnEInline(admin.TabularInline):
            model = TwoAlbumFKAndAnE
            fk_name = "album1"

        class MyAdmin(admin.ModelAdmin):
            inlines = [TwoAlbumFKAndAnEInline]

        errors = MyAdmin(Album, AdminSite()).check()
        self.assertEqual(errors, [])