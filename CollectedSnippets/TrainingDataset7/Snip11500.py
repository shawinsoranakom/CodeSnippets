def fetch_one(self, instance):
        rel_obj = self.get_object(instance)
        self.field.set_cached_value(instance, rel_obj)
        # If this is a one-to-one relation, set the reverse accessor cache on
        # the related object to the current instance to avoid an extra SQL
        # query if it's accessed later on.
        remote_field = self.field.remote_field
        if not remote_field.multiple:
            remote_field.set_cached_value(rel_obj, instance)