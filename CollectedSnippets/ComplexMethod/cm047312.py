def create(self, vals_list):
        field_ids = {vals['field_id'] for vals in vals_list}
        field_names = set()
        for field in self.env['ir.model.fields'].browse(field_ids):
            field_names.add((field.model, field.name))
            if field.state != 'manual':
                raise UserError(_('Properties of base fields cannot be altered in this manner! '
                                  'Please modify them through Python code, '
                                  'preferably through a custom addon!'))
        recs = super().create(vals_list)

        model_names = OrderedSet(
            model
            for model, name in field_names
            if model in self.pool and name in self.pool[model]._fields
        )
        if model_names:
            # setup models; this re-initializes model in registry
            self.env.flush_all()
            self.pool._setup_models__(self.env.cr, model_names)

        return recs