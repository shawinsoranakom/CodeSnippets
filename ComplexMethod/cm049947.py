def _add_values(self, values, model_name, index=None):
        """Adds values to the store for a given model name and index."""
        target = self.data[model_name][index] if index else self.data[model_name]
        for key, val in values.items():
            assert key != "_DELETE", f"invalid key {key} in {model_name}: {values}"
            if isinstance(val, Store.Relation):
                val._add_to_store(self, target, key)
            elif isinstance(val, datetime):
                target[key] = odoo.fields.Datetime.to_string(val)
            elif isinstance(val, date):
                target[key] = odoo.fields.Date.to_string(val)
            elif isinstance(val, Markup):
                target[key] = ["markup", str(val)]
            else:
                target[key] = val