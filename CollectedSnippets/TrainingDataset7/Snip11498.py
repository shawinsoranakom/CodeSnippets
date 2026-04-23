def get_object(self, instance):
        qs = self.get_queryset(instance=instance)
        # Assuming the database enforces foreign keys, this won't fail.
        return qs.get(self.field.get_reverse_related_filter(instance))