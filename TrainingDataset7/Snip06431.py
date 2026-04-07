def __get__(self, instance, cls=None):
        if instance is None:
            return self

        # Don't use getattr(instance, self.ct_field) here because that might
        # reload the same ContentType over and over (#5570). Instead, get the
        # content type ID here, and later when the actual instance is needed,
        # use ContentType.objects.get_for_id(), which has a global cache.
        f = self.field.model._meta.get_field(self.field.ct_field)
        ct_id = getattr(instance, f.attname, None)
        pk_val = getattr(instance, self.field.fk_field)

        rel_obj = self.field.get_cached_value(instance, default=None)
        if rel_obj is None and self.field.is_cached(instance):
            return rel_obj
        if rel_obj is not None:
            ct_match = (
                ct_id
                == self.field.get_content_type(obj=rel_obj, using=instance._state.db).id
            )
            pk_match = ct_match and rel_obj._meta.pk.to_python(pk_val) == rel_obj.pk
            if pk_match:
                return rel_obj
            else:
                rel_obj = None

        instance._state.fetch_mode.fetch(self, instance)
        return self.field.get_cached_value(instance)