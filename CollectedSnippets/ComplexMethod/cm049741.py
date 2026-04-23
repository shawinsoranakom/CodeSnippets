def _compute_notified_bcc_contains_share(self):
        """ When being in monorecord comment mode, compute 'bcc' which are
        followers that are going to be 'silently' notified by the message. """
        post_composers = self.filtered(
            lambda comp: comp.model and comp.composition_mode == 'comment' and not comp.composition_batch
        )
        (self - post_composers).notified_bcc_contains_share = False
        for composer in post_composers:
            record = self.env[composer.model].browse(
                composer._evaluate_res_ids()[:1]
            )
            recipients_data = self.env['mail.followers']._get_recipient_data(
                record, composer.message_type, composer.subtype_id.id
            )[record.id]
            # Since it is only an informative field let's accept duplicates with partner_ids field
            partner_ids = [
                pid
                for pid, pdata in recipients_data.items()
                if (pid and pdata['active']
                    and pid != self.env.user.partner_id.id)
            ]
            notified_bcc = self.env['res.partner'].search([('id', 'in', partner_ids)])
            composer.notified_bcc_contains_share = any(notified_bcc.mapped('partner_share'))