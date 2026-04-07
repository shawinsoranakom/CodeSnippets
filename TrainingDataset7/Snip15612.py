def formfield_for_manytomany(self, db_field, request, **kwargs):
                if db_field.name == "other_interpreters":
                    kwargs["queryset"] = Band.objects.filter(rank__gt=2)
                return super().formfield_for_foreignkey(db_field, request, **kwargs)