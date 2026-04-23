def write(self, vals):
        # user_id change: update date_open
        if vals.get('user_id'):
            vals['date_open'] = fields.Datetime.now()
        old_interviewers = self.interviewer_ids
        # stage_id: track last stage before update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
            for applicant in self:
                vals['last_stage_id'] = applicant.stage_id.id
                new_stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
                if new_stage.hired_stage and not applicant.stage_id.hired_stage:
                    if applicant.job_id.no_of_recruitment > 0:
                        applicant.job_id.no_of_recruitment -= 1
                elif not new_stage.hired_stage and applicant.stage_id.hired_stage:
                    applicant.job_id.no_of_recruitment += 1
        # kanban_state: also set date_last_stage_update
        if 'kanban_state' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
        res = super().write(vals)

        for applicant in self:
            if applicant.pool_applicant_id and applicant != applicant.pool_applicant_id and (not applicant.is_pool_applicant):
                if 'email_from' in vals:
                    applicant.pool_applicant_id.email_from = vals['email_from']
                if 'partner_phone' in vals:
                    applicant.pool_applicant_id.partner_phone = vals['partner_phone']
                if 'linkedin_profile' in vals:
                    applicant.pool_applicant_id.linkedin_profile = vals['linkedin_profile']
                if 'type_id' in vals:
                    applicant.pool_applicant_id.type_id = vals['type_id']

        if 'interviewer_ids' in vals:
            interviewers_to_clean = old_interviewers - self.interviewer_ids
            interviewers_to_clean._remove_recruitment_interviewers()
            self.sudo().interviewer_ids._create_recruitment_interviewers()

            new_interviewers = self.interviewer_ids - old_interviewers - self.env.user
            if new_interviewers:
                for applicant in self:
                    notification_subject = _("You have been assigned as an interviewer for %s", applicant.display_name)
                    notification_body = _("You have been assigned as an interviewer for the Applicant %s", applicant.partner_name)
                    applicant.message_notify(
                        res_id=applicant.id,
                        model=applicant._name,
                        partner_ids=new_interviewers.partner_id.ids,
                        author_id=self.env.user.partner_id.id,
                        email_from=self.env.user.email_formatted,
                        subject=notification_subject,
                        body=notification_body,
                        email_layout_xmlid="mail.mail_notification_layout",
                        model_description="Applicant",
                    )
        return res