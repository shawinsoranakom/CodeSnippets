def default_get(self, fields):
        # super default_model='crm.lead' for easier use in addons
        context = dict(self.env.context)
        if context.get('default_res_model') and not context.get('default_res_model_id'):
            context.update(
                default_res_model_id=self.env['ir.model']._get_id(context['default_res_model'])
            )
        if context.get('default_res_model_id') and not context.get('default_res_model'):
            context.update(
                default_res_model=self.env['ir.model'].browse(self.env.context['default_res_model_id']).sudo().model
            )

        defaults = super(CalendarEvent, self.with_context(context)).default_get(fields)

        # support active_model / active_id as replacement of default_* if not already given
        if 'res_model_id' not in defaults and 'res_model_id' in fields and \
                context.get('active_model') and context['active_model'] != 'calendar.event':
            defaults['res_model_id'] = self.env['ir.model']._get_id(context['active_model'])
            defaults['res_model'] = context.get('active_model')
        if 'res_id' not in defaults and 'res_id' in fields and \
                defaults.get('res_model_id') and context.get('active_id'):
            defaults['res_id'] = context['active_id']

        return defaults