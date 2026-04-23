def local_setter(final_field, obj, from_obj):
                # Set a reverse fk object when relation is non-empty.
                if from_obj:
                    final_field.remote_field.set_cached_value(from_obj, obj)