def test_fk_exclusion(self):
        """
        Regression test for #11709 - when testing for fk excluding (when
        exclude is given) make sure fk_name is honored or things blow up when
        there is more than one fk to the parent model.
        """

        class TwoAlbumFKAndAnEInline(admin.TabularInline):
            model = TwoAlbumFKAndAnE
            exclude = ("e",)
            fk_name = "album1"

        class MyAdmin(admin.ModelAdmin):
            inlines = [TwoAlbumFKAndAnEInline]

        errors = MyAdmin(Album, AdminSite()).check()
        self.assertEqual(errors, [])