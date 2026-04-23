def _prepare_mail_values_rendered(self, res_ids):
        """Generate values that are already rendered. This is used mainly in
        monorecord mode, when the wizard contains value already generated
        (e.g. "Send by email" on a sale order, in form view).

        :param list res_ids: list of record IDs on which composer runs;

        :returns: for each res_id, the generated values used to
          populate in '_prepare_mail_values';
        :rtype: dict
        """
        self.ensure_one()
        email_mode = self.composition_mode == 'mass_mail'

        # Duplicate attachments linked to the email.template. Indeed, composer
        # duplicates attachments in mass mode. But in 'rendered' mode attachments
        # may come from an email template (same IDs). They also have to be
        # duplicated to avoid changing their ownership.
        if self.composition_mode == 'comment' and self.template_id and self.attachment_ids:
            new_attachment_ids = []
            for attachment in self.attachment_ids:
                if attachment in self.template_id.attachment_ids:
                    new_attachment_ids.append(attachment.copy({
                        'res_model': 'mail.compose.message',
                        'res_id': self.id,
                    }).id)
                else:
                    new_attachment_ids.append(attachment.id)
            new_attachment_ids.reverse()
            self.write({'attachment_ids': [Command.set(new_attachment_ids)]})

        return {
            res_id: {
                'attachment_ids': [attach.id for attach in self.attachment_ids],
                'body': self.body or '',
                'email_from': self.email_from,
                'partner_ids': self.partner_ids.ids,
                'scheduled_date': self.scheduled_date,
                'subject': self.subject or '',
                **(
                    {
                        # notify parameter to force layout lang
                        'force_email_lang': self.lang,
                    } if not email_mode else {}
                ),
                # do not send void reply_to, force only given value
                **({'reply_to': self.reply_to} if self.reply_to else {}),
            }
            for res_id in res_ids
        }