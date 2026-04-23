def write(self, vals):
        if not self:
            return True

        if (
            not self.env.user._is_admin() and
            any(record.field_id.state != 'manual' for record in self)
        ):
            raise UserError(_('Properties of base fields cannot be altered in this manner! '
                              'Please modify them through Python code, '
                              'preferably through a custom addon!'))

        if 'value' in vals:
            for selection in self:
                if selection.value == vals['value']:
                    continue
                if selection.field_id.store:
                    # in order to keep the cache consistent, flush the
                    # corresponding field, and invalidate it from cache
                    model = self.env[selection.field_id.model]
                    fname = selection.field_id.name
                    model.invalidate_model([fname])
                    # replace the value by the new one in the field's corresponding column
                    query = f'UPDATE "{model._table}" SET "{fname}"=%s WHERE "{fname}"=%s'
                    self.env.cr.execute(query, [vals['value'], selection.value])

        result = super().write(vals)

        # setup models; this re-initializes model in registry
        self.env.flush_all()
        model_names = self.field_id.model_id.mapped('model')
        self.pool._setup_models__(self.env.cr, model_names)

        return result