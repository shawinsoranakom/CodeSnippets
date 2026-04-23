def check_and_update_obj(obj):
                if not isinstance(obj, self.model):
                    raise TypeError(
                        "'%s' instance expected, got %r"
                        % (self.model._meta.object_name, obj)
                    )
                setattr(obj, self.content_type_field_name, self.content_type)
                setattr(obj, self.object_id_field_name, self.pk_val)