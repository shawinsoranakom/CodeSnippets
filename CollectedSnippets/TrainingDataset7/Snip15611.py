def formfield_for_foreignkey(self, db_field, request, **kwargs):
                if db_field.name == "band":
                    kwargs["queryset"] = Band.objects.filter(rank__gt=2)
                return super().formfield_for_foreignkey(db_field, request, **kwargs)