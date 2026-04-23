def create(self, vals_list):
        IrModel = self.env['ir.model']
        for vals in vals_list:
            if vals.get('translate') and not isinstance(vals['translate'], str):
                _logger.warning("Deprecated since Odoo 19, ir.model.fields.translate becomes Selection, the value should be a string")
                vals['translate'] = 'html_translate' if vals.get('ttype') == 'html' else 'standard'
            if 'model_id' in vals:
                vals['model'] = IrModel.browse(vals['model_id']).model

        # for self._get_ids() in _update_selection()
        self.env.registry.clear_cache('stable')

        res = super().create(vals_list)
        models = OrderedSet(res.mapped('model'))

        for vals in vals_list:
            if vals.get('state', 'manual') == 'manual':
                relation = vals.get('relation')
                if relation and not IrModel._get_id(relation):
                    raise UserError(_("Model %s does not exist!", vals['relation']))

                if (
                    vals.get('ttype') == 'one2many' and
                    vals.get("store", True) and
                    not vals.get("related") and
                    not self.search_count([
                        ('ttype', '=', 'many2one'),
                        ('model', '=', vals['relation']),
                        ('name', '=', vals['relation_field']),
                    ])
                ):
                    raise UserError(_("Many2one %(field)s on model %(model)s does not exist!", field=vals['relation_field'], model=vals['relation']))

        if any(model in self.pool for model in models):
            # setup models; this re-initializes model in registry
            self.env.flush_all()
            self.pool._setup_models__(self.env.cr, models)
            # update database schema of models and their descendants
            models = self.pool.descendants(models, '_inherits')
            self.pool.init_models(self.env.cr, models, dict(self.env.context, update_custom_fields=True))

        return res