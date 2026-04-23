def _prepare_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create either
         mail_messages or mail_mails depending on composition mode.

        Some summarized information on generation: mail versus message fields
        (or both), and static (never rendered) versus dynamic (raw or rendered).

        MAIL
            STA - 'auto_delete',
            DYN - 'body_html',
            STA - 'force_send',  (notify parameter)
            STA - 'model',
            DYN - 'recipient_ids',  (from partner_ids)
            DYN - 'res_id',
            STA - 'is_notification',

        MESSAGE
            DYN - 'body',
            STA - 'email_add_signature',
            STA - 'email_layout_xmlid',
            DYN - 'force_email_lang',  # notify parameter
            STA - 'record_alias_domain_id',  # monorecord only
            STA - 'record_company_id',  # monorecord only

        BOTH
            DYN - 'attachment_ids',
            STA - 'author_id',  (to improve with template)
            DYN - 'email_from',
            STA - 'mail_activity_type_id',
            STA - 'mail_server_id',
            STA - 'message_type',
            STA - 'parent_id',
            DYN - 'partner_ids',
            DYN - 'reply_to',
            STA - 'reply_to_force_new',
            DYN - 'scheduled_date',
            DYN - 'subject',
            STA - 'subtype_id',

        :param list res_ids: list of record IDs on which composer runs;

        :return: for each res_id, values to create the mail.mail or to
          give to message_post, depending on composition mode;
        :rtype: dict
        """
        self.ensure_one()
        email_mode = self.composition_mode == 'mass_mail'
        rendering_mode = email_mode or self.composition_batch

        # values that do not depend on rendering mode
        base_values = self._prepare_mail_values_static()

        additional_values_all = {}
        # rendered based on raw content (wizard or template)
        if rendering_mode and self.model:
            additional_values_all = self._prepare_mail_values_dynamic(res_ids)
        # wizard content already rendered
        elif not rendering_mode:
            additional_values_all = self._prepare_mail_values_rendered(res_ids)

        mail_values_all = {
            res_id: dict(
                base_values,
                **additional_values_all.get(res_id, {})
            )
            for res_id in res_ids
        }

        if email_mode:
            mail_values_all = self._process_mail_values_state(mail_values_all)
            # based on previous values, compute message ID / references
            for res_id, mail_values in mail_values_all.items():
                # generate message_id directly; instead of letting mail_message create
                # method doing it. Then use it to craft references, allowing to keep
                # a trace of message_id even when email providers override it.
                # Note that if 'auto_delete' is set and if 'auto_delete_keep_log' is False,
                # mail.message is removed and parent finding based on messageID
                # may be broken, tough life
                message_id = self.env['mail.message']._get_message_id(mail_values)
                mail_values['message_id'] = message_id
                mail_values['references'] = message_id
        return mail_values_all