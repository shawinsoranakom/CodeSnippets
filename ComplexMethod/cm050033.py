def default_get(self, fields):
        self_ctx = self
        if self.env.context.get('default_applicant_id'):
            self_ctx = self.with_context(
                default_res_model='hr.applicant',  # res_model seems to be lost without this
                default_res_model_id=self.env.ref('hr_recruitment.model_hr_applicant').id,
                default_res_id=self.env.context.get('default_applicant_id'),
                default_partner_ids=self.env.context.get('default_partner_ids'),
                default_name=self.env.context.get('default_name')
            )

        defaults = super(CalendarEvent, self_ctx).default_get(fields)

        # sync res_model / res_id to opportunity id (aka creating meeting from lead chatter)
        if 'applicant_id' not in defaults:
            res_model = defaults.get('res_model', False) or self_ctx.env.context.get('default_res_model')
            res_model_id = defaults.get('res_model_id', False) or self_ctx.env.context.get('default_res_model_id')
            if (res_model and res_model == 'hr.applicant') or (res_model_id and self_ctx.env['ir.model'].sudo().browse(res_model_id).model == 'hr.applicant'):
                defaults['applicant_id'] = defaults.get('res_id', False) or self_ctx.env.context.get('default_res_id', False)

        return defaults