def action_refuse_reason_apply(self):
        if self.send_mail:
            if not self.env.user.email:
                raise UserError(_("Unable to post message, please configure the sender's email address."))
            if any(not (applicant.email_from or applicant.partner_id.email) for applicant in self.applicant_ids):
                raise UserError(_("At least one applicant doesn't have a email; you can't use send email option."))

        refused_applications = self.applicant_ids
        if self.duplicates_count and self.duplicates:
            refused_applications |= self.duplicate_applicant_ids

            original_applicant_by_duplicate_applicant = self._get_related_original_applicants()
            message_by_duplicate_applicant = {}
            for duplicate_applicant in self.duplicate_applicant_ids:
                url = original_applicant_by_duplicate_applicant[duplicate_applicant]._get_html_link()
                message_by_duplicate_applicant[duplicate_applicant.id] = _(
                    "Refused automatically because this application has been identified as a duplicate of %(link)s",
                    link=url)
            self.duplicate_applicant_ids._message_log_batch(bodies={
                    duplicate.id: message_by_duplicate_applicant[duplicate.id]
                    for duplicate in self.duplicate_applicant_ids
                }
            )
        refused_applications.write({'refuse_reason_id': self.refuse_reason_id.id, 'active': False, 'refuse_date': datetime.now()})

        if self.send_mail:
            self._prepare_send_refusal_mails()

        return {'type': 'ir.actions.act_window_close'}