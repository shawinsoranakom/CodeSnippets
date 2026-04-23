def write(self, vals):
        if self and ('is_mail_thread' in vals or 'is_mail_activity' in vals or 'is_mail_blacklist' in vals):
            if any(rec.state != 'manual' for rec in self):
                raise UserError(_('Only custom models can be modified.'))
            if 'is_mail_thread' in vals and any(rec.is_mail_thread > vals['is_mail_thread'] for rec in self):
                raise UserError(_('Field "Mail Thread" cannot be changed to "False".'))
            if 'is_mail_activity' in vals and any(rec.is_mail_activity > vals['is_mail_activity'] for rec in self):
                raise UserError(_('Field "Mail Activity" cannot be changed to "False".'))
            if 'is_mail_blacklist' in vals and any(rec.is_mail_blacklist > vals['is_mail_blacklist'] for rec in self):
                raise UserError(_('Field "Mail Blacklist" cannot be changed to "False".'))
            res = super(IrModel, self).write(vals)
            self.env.flush_all()
            # setup models; this reloads custom models in registry
            model_names = self.mapped('model')
            self.pool._setup_models__(self.env.cr, model_names)
            # update database schema of models
            model_names = self.pool.descendants(model_names, '_inherits')
            self.pool.init_models(self.env.cr, model_names, dict(self.env.context, update_custom_fields=True))
        else:
            res = super(IrModel, self).write(vals)
        return res