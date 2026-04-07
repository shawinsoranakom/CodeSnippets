def fetch_one(self, instance):
        # Kept for backwards compatibility with overridden
        # get_forward_related_filter()
        filter_args = self.related.field.get_forward_related_filter(instance)
        try:
            rel_obj = self.get_queryset(instance=instance).get(**filter_args)
        except self.related.related_model.DoesNotExist:
            rel_obj = None
        else:
            self.related.field.set_cached_value(rel_obj, instance)
        self.related.set_cached_value(instance, rel_obj)