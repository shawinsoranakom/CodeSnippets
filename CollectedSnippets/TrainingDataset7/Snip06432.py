def fetch_one(self, instance):
        f = self.field.model._meta.get_field(self.field.ct_field)
        ct_id = getattr(instance, f.attname, None)
        pk_val = getattr(instance, self.field.fk_field)
        rel_obj = None
        if ct_id is not None:
            ct = self.field.get_content_type(id=ct_id, using=instance._state.db)
            try:
                rel_obj = ct.get_object_for_this_type(
                    using=instance._state.db, pk=pk_val
                )
            except ObjectDoesNotExist:
                pass
            else:
                rel_obj._state.fetch_mode = instance._state.fetch_mode
        self.field.set_cached_value(instance, rel_obj)