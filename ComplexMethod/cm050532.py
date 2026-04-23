def _ensure_fields_write(self, vals, defaults=False):
        if defaults:
            vals = {
                **{
                    key[8:]: value
                    for key, value in self.env.context.items()
                    if key.startswith("default_") and key[8:] in self._fields
                },
                **vals
            }

        for fname, value in vals.items():
            field = self._fields.get(fname)
            if field and field.type == 'many2one':
                self.env[field.comodel_name].browse(value).check_access('read')