def write(self, vals):
        old_interviewers = self.interviewer_ids
        old_managers = {}
        old_recruiters = {}
        for job in self:
            old_managers[job] = job.manager_id
            old_recruiters[job] = job.user_id
        if 'active' in vals and not vals['active']:
            self.application_ids.active = False
        res = super().write(vals)
        if 'interviewer_ids' in vals:
            interviewers_to_clean = old_interviewers - self.interviewer_ids
            interviewers_to_clean._remove_recruitment_interviewers()
            self.sudo().interviewer_ids._create_recruitment_interviewers()

        # Subscribe the recruiter if it has changed.
        if "user_id" in vals:
            for job in self:
                to_unsubscribe = [
                    partner
                    for partner in old_recruiters[job].partner_id.ids
                    if partner not in job.manager_id._get_related_partners().ids
                ]
                job.message_unsubscribe(to_unsubscribe)
                application_ids = job.application_ids.filtered(
                    lambda x:
                        x.user_id == old_recruiters[job] and
                        x.application_status == 'ongoing'
                )
                if application_ids:
                    application_ids.message_unsubscribe(to_unsubscribe)
                    application_ids.with_context(mail_auto_subscribe_no_notify=True).user_id = job.user_id

        # Since the alias is created upon record creation, the default values do not reflect the current values unless
        # specifically rewritten
        # List of fields to keep synched with the alias
        alias_fields = {'department_id', 'user_id'}
        if any(field for field in alias_fields if field in vals):
            for job in self:
                alias_default_vals = job._alias_get_creation_values().get('alias_defaults', '{}')
                job.alias_defaults = alias_default_vals
        return res