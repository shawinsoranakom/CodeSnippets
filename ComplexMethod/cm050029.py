def create(self, vals_list):
        for vals in vals_list:
            if vals.get('user_id'):
                vals['date_open'] = fields.Datetime.now()
            if vals.get('email_from'):
                vals['email_from'] = vals['email_from'].strip()
        applicants = super().create(vals_list)
        applicants.sudo().interviewer_ids._create_recruitment_interviewers()

        for applicant in applicants:
            if applicant.talent_pool_ids and not applicant.pool_applicant_id:
                applicant.pool_applicant_id = applicant

        if (applicants.interviewer_ids.partner_id - self.env.user.partner_id):
            for applicant in applicants:
                interviewers_to_notify = applicant.interviewer_ids.partner_id - self.env.user.partner_id
                notification_subject = _("You have been assigned as an interviewer for %s", applicant.display_name)
                notification_body = _("You have been assigned as an interviewer for the Applicant %s", applicant.partner_name)
                applicant.message_notify(
                    res_id=applicant.id,
                    model=applicant._name,
                    partner_ids=interviewers_to_notify.ids,
                    author_id=self.env.user.partner_id.id,
                    email_from=self.env.user.email_formatted,
                    subject=notification_subject,
                    body=notification_body,
                    email_layout_xmlid="mail.mail_notification_layout",
                    model_description="Applicant",
                )
        return applicants