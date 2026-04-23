def _inverse_partner_email(self):
        for applicant in self:
            email_normalized = tools.email_normalize(applicant.email_from or '')
            if not email_normalized:
                continue
            if not applicant.partner_id:
                if not applicant.partner_name:
                    raise UserError(_("You must define a Contact Name for this applicant."))
                applicant.partner_id = applicant._partner_find_from_emails_single(
                    [applicant.email_from], no_create=False,
                    additional_values={
                        email_normalized: {'lang': self.env.lang}
                    },
                )
            if applicant.partner_name and applicant.partner_name != applicant.partner_id.name:
                applicant.partner_id.name = applicant.partner_name
            if email_normalized and email_normalized != applicant.partner_id.email:
                applicant.partner_id.email = applicant.email_from
            if applicant.partner_phone and applicant.partner_phone != applicant.partner_id.phone:
                applicant.partner_id.phone = applicant.partner_phone