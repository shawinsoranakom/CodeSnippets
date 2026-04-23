def _action_send_mail(self, res_ids=None):
        odoobot = self.env.ref('base.partner_root')
        user_partner = self.env.user.partner_id

        for mailing in self:
            context_user = mailing.user_id or mailing.write_uid or self.env.user
            mailing = mailing.with_context(
                **self.env['res.users'].with_user(context_user).context_get()
            )
            mailing_res_ids = res_ids or mailing._get_remaining_recipients()
            if not mailing_res_ids:
                raise UserError(_('There are no recipients selected.'))

            composer_values = {
                'auto_delete': not mailing.keep_archives,
                # email-mode: keep original message for routing
                'auto_delete_keep_log': mailing.reply_to_mode == 'update',
                # If current user is odoobot, use mailing responsible (no impact on email_from)
                'author_id': mailing.user_id.partner_id.id if user_partner == odoobot else user_partner.id,
                'attachment_ids': [(4, attachment.id) for attachment in mailing.attachment_ids],
                'body': mailing._prepend_preview(mailing.body_html or '', mailing.preview),
                'composition_mode': 'mass_mail',
                'email_from': mailing.email_from,
                'mail_server_id': mailing.mail_server_id.id,
                'mailing_list_ids': [(4, l.id) for l in mailing.contact_list_ids],
                'mass_mailing_id': mailing.id,
                'model': mailing.mailing_model_real,
                'reply_to_force_new': mailing.reply_to_mode == 'new',
                'subject': mailing.subject,
                'template_id': False,
                'use_exclusion_list': mailing.use_exclusion_list,
            }
            if mailing.reply_to_mode == 'new':
                composer_values['reply_to'] = mailing.reply_to

            composer = self.env['mail.compose.message'].with_context(
                active_ids=mailing_res_ids,
                default_composition_mode='mass_mail',
                **mailing._get_mass_mailing_context()
            ).create(composer_values)

            # auto-commit except in testing mode
            auto_commit = not modules.module.current_test
            composer._action_send_mail(auto_commit=auto_commit)

            mailing.write({
                'state': 'done',
                'sent_date': fields.Datetime.now(),
                # send the KPI mail only if it's the first sending
                'kpi_mail_required': not mailing.sent_date,
            })

            # ensure mailing state update after auto-commit
            if auto_commit is True:
                self.env.cr.commit()

        return True