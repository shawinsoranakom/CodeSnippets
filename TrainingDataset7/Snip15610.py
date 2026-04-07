def test_custom_queryset_still_wins(self):
        """Custom queryset has still precedence (#21405)"""

        class SongAdmin(admin.ModelAdmin):
            # Exclude one of the two Bands from the querysets
            def formfield_for_foreignkey(self, db_field, request, **kwargs):
                if db_field.name == "band":
                    kwargs["queryset"] = Band.objects.filter(rank__gt=2)
                return super().formfield_for_foreignkey(db_field, request, **kwargs)

            def formfield_for_manytomany(self, db_field, request, **kwargs):
                if db_field.name == "other_interpreters":
                    kwargs["queryset"] = Band.objects.filter(rank__gt=2)
                return super().formfield_for_foreignkey(db_field, request, **kwargs)

        class StaticOrderingBandAdmin(admin.ModelAdmin):
            ordering = ("rank",)

        site.unregister(Song)
        site.register(Song, SongAdmin)
        site.register(Band, StaticOrderingBandAdmin)

        self.check_ordering_of_field_choices([self.b2])