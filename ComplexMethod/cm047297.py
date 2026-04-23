def write(self, vals):
        for unmodifiable_field in ('model', 'state', 'abstract', 'transient'):
            if unmodifiable_field in vals and any(rec[unmodifiable_field] != vals[unmodifiable_field] for rec in self):
                raise UserError(_('Field %s cannot be modified on models.', self._fields[unmodifiable_field]._description_string(self.env)))
        # Filter out operations 4 from field id, because the web client always
        # writes (4,id,False) even for non dirty items.
        if 'field_id' in vals:
            vals['field_id'] = [op for op in vals['field_id'] if op[0] != 4]
        res = super().write(vals)
        # ordering has been changed, reload registry to reflect update + signaling
        if 'order' in vals or 'fold_name' in vals:
            self.env.flush_all()  # _setup_models__ need to fetch the updated values from the db
            # incremental setup will reload custom models
            self.pool._setup_models__(self.env.cr, [])
        return res