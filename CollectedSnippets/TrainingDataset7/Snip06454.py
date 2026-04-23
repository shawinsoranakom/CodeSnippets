def gfk_key(obj):
            ct_id = getattr(obj, ct_attname)
            if ct_id is None:
                return None
            else:
                model = self.field.get_content_type(
                    id=ct_id, using=obj._state.db
                ).model_class()
                return str(getattr(obj, self.field.fk_field)), model