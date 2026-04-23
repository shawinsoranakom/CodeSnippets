def _message_post_after_hook(self, message, msg_vals):
        #  OVERRIDE
        #  If no partner is set on track when sending a message, then we create one from suggested contact selected.
        #  If one or more have been created from chatter (Suggested Recipients) we search for the expected one and write the partner_id on track.
        if msg_vals.get('partner_ids') and not self.partner_id:
            #  Contact(s) created from chatter set on track : we verify if at least one is the expected contact
            #  linked to the track. (created from contact_email if any, then partner_email if any)
            main_email = self.contact_email or self.partner_email
            main_email_normalized = tools.email_normalize(main_email)
            new_partner = message.partner_ids.filtered(
                lambda partner: partner.email == main_email or (main_email_normalized and partner.email_normalized == main_email_normalized)
            )
            if new_partner:
                mail_email_fname = 'contact_email' if self.contact_email else 'partner_email'
                if new_partner[0].email_normalized:
                    email_domain = (mail_email_fname, 'in', [new_partner[0].email, new_partner[0].email_normalized])
                else:
                    email_domain = (mail_email_fname, '=', new_partner[0].email)
                self.search([
                    ('partner_id', '=', False), email_domain, ('stage_id.is_cancel', '=', False),
                ]).write({'partner_id': new_partner[0].id})
        return super()._message_post_after_hook(message, msg_vals)