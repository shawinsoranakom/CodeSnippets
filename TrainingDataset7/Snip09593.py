def _delete_composed_index(self, model, fields, *args):
        self._create_missing_fk_index(model, fields=fields)
        return super()._delete_composed_index(model, fields, *args)