def _prepare_for_bulk_create(self, objs):
        objs_with_pk, objs_without_pk = [], []
        for obj in objs:
            if isinstance(obj.pk, DatabaseDefault):
                objs_without_pk.append(obj)
            elif obj._is_pk_set():
                objs_with_pk.append(obj)
            else:
                obj.pk = obj._meta.pk.get_pk_value_on_save(obj)
                if obj._is_pk_set():
                    objs_with_pk.append(obj)
                else:
                    objs_without_pk.append(obj)
            obj._prepare_related_fields_for_save(operation_name="bulk_create")
        return objs_with_pk, objs_without_pk