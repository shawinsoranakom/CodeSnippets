def message_new(self, msg_dict, custom_values=None):
        # Remove default author when going through the mail gateway. Indeed, we
        # do not want to explicitly set user_id to False; however we do not
        # want the gateway user to be responsible if no other responsible is
        # found.
        self = self.with_context(default_user_id=False)
        stage = False
        if custom_values and 'job_id' in custom_values:
            job = self.env['hr.job'].browse(custom_values['job_id'])
            stage = job._get_first_stage()

        partner_name, email_from_normalized = tools.parse_contact_from_email(msg_dict.get('from'))

        defaults = {
            'partner_name': partner_name,
        }
        job_platform = self.env['hr.job.platform'].search([('email', '=', email_from_normalized)], limit=1)

        if msg_dict.get('from') and not job_platform:
            defaults['email_from'] = msg_dict.get('from')
            defaults['partner_id'] = msg_dict.get('author_id', False)
        if msg_dict.get('email_from') and job_platform:
            subject_pattern = re.compile(job_platform.regex or '')
            regex_results = re.findall(subject_pattern, msg_dict.get('subject')) + re.findall(subject_pattern, msg_dict.get('body'))
            defaults['partner_name'] = regex_results[0] if regex_results else partner_name
            del msg_dict['email_from']
        if msg_dict.get('priority'):
            defaults['priority'] = msg_dict.get('priority')
        if stage and stage.id:
            defaults['stage_id'] = stage.id
        if custom_values:
            defaults.update(custom_values)
        res = super().message_new(msg_dict, custom_values=defaults)
        res._compute_partner_phone_email()
        return res