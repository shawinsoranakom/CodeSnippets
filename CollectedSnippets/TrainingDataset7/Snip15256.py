def test_extra(self):
        class SongAdmin(admin.ModelAdmin):
            @admin.display
            def awesome_song(self, instance):
                if instance.title == "Born to Run":
                    return "Best Ever!"
                return "Status unknown."

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])