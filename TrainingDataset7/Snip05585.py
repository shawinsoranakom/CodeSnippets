def _check_relation(self, obj, parent_model):
        try:
            _get_foreign_key(parent_model, obj.model, fk_name=obj.fk_name)
        except ValueError as e:
            return [checks.Error(e.args[0], obj=obj.__class__, id="admin.E202")]
        else:
            return []