def _prepare_mail_values_dynamic(self, res_ids):
        """Generate values based on composer content as well as its template
        based on records given by res_ids.

        Part of the advanced rendering is delegated to template, notably
        recipients or attachments dynamic generation. See sub methods for
        more details.

        :param list res_ids: list of record IDs on which composer runs;

        :returns: for each res_id, the generated values used to
          populate in '_prepare_mail_values';
        :rtype: dict
        """
        self.ensure_one()
        RecordsModel = self.env[self.model].with_prefetch(res_ids)
        email_mode = self.composition_mode == 'mass_mail'

        # records values
        companies = RecordsModel.browse(res_ids)._mail_get_companies(default=self.env.company)
        alias_domains = RecordsModel.browse(res_ids)._mail_get_alias_domains(default_company=self.env.company)

        # langs, used currently only to propagate in comment mode for notification
        # layout translation
        langs = self._render_lang(res_ids)
        subjects = self._render_field('subject', res_ids, compute_lang=True)
        bodies = self._render_field(
            'body', res_ids, compute_lang=True,
            # We want to preserve comments in emails so as to keep mso conditionals
            options={'preserve_comments': email_mode},
        )
        emails_from = self._render_field('email_from', res_ids)

        mail_values_all = {
            res_id: {
                'body': bodies[res_id],  # should be void
                'email_from': emails_from[res_id],
                'scheduled_date': False,
                'subject': subjects[res_id],
                # record-specific environment values (company, alias_domain)
                'record_alias_domain_id': alias_domains[res_id].id,
                'record_company_id': companies[res_id].id,
                # some fields are specific to mail
                **(
                    {
                        'body_html': bodies[res_id],
                        'res_id': res_id,
                    } if email_mode else {}
                ),
                # some fields are specific to message
                **(
                    {
                        # notify parameter to force layout lang
                        'force_email_lang': langs[res_id],
                    } if not email_mode else {}
                ),
            }
            for res_id in res_ids
        }

        # generate template-based values
        if self.template_id:
            template_values = self._generate_template_for_composer(
                res_ids,
                ['attachment_ids',
                 'email_to',
                 'email_cc',
                 'partner_ids',
                 'report_template_ids',
                 'scheduled_date',
                ],
                allow_suggested=(
                    self.composition_mode == 'comment' and not self.composition_batch and
                    self.message_type == 'comment' and not self.subtype_is_log
                ),
                find_or_create_partners=self.env.context.get("mail_composer_force_partners", True),
            )
            for res_id in res_ids:
                # remove attachments from template values as they should not be rendered
                template_values[res_id].pop('attachment_ids', None)
                mail_values_all[res_id].update(template_values[res_id])

        # Handle recipients. Without template, if no partner_ids is given, update
        # recipients using default recipients to be sure to notify someone
        if not self.template_id and not self.partner_ids and email_mode:
            default_recipients = RecordsModel.browse(res_ids)._message_get_default_recipients()
            for res_id in res_ids:
                mail_values_all[res_id].update(
                    default_recipients.get(res_id, {})
                )
        # TDE FIXME: seems to be missing an "else" here to add partner_ids in rendering mode

        # Handle reply-to. In update mode (force_new False), reply-to value is
        # computed from the records (to have their alias). In new mode, reply-to
        # is coming from reply_to field to render.
        if not self.reply_to_force_new:
            # compute alias-based reply-to in batch
            reply_to_values = RecordsModel.browse(res_ids)._notify_get_reply_to_batch(
                defaults=emails_from,
                author_ids={res_id: self.author_id.id for res_id in res_ids},
            )
        if self.reply_to_force_new:
            reply_to_values = self._render_field('reply_to', res_ids)

        # Handle per-record update
        for res_id, mail_values in mail_values_all.items():
            record = RecordsModel.browse(res_id)

            # attachments. Copy attachment_ids (each has its own copies), and decode
            # attachments as required by _process_attachments_for_post
            attachment_ids = self.attachment_ids.copy({'res_model': self._name, 'res_id': self.id}).ids
            attachment_ids.reverse()
            decoded_attachments = [
                (name, base64.b64decode(enc_cont))
                for name, enc_cont in mail_values.pop('attachments', [])
            ]
            # email_mode: prepare processed attachments as commands for mail.mail
            if email_mode:
                process_record = record if hasattr(record, "_process_attachments_for_post") else record.env["mail.thread"]
                mail_values['attachment_ids'] = process_record._process_attachments_for_post(
                    decoded_attachments,
                    attachment_ids,
                    {'model': 'mail.message', 'res_id': 0} if (
                        not hasattr(record, "_process_attachments_for_post")
                        or (self.auto_delete and not self.auto_delete_keep_log)
                    ) else {}  # link to record if kept in chatter, for ease of access
                )['attachment_ids']
            # comment mode: prepare attachments as a list of IDs, to be processed by MailThread
            else:
                mail_values['attachments'] = decoded_attachments
                mail_values['attachment_ids'] = attachment_ids

            # headers
            if email_mode:
                mail_values['headers'] = repr(record._notify_by_email_get_headers())

            # recipients: transform partner_ids (field used in mail_message) into
            # recipient_ids, used by mail_mail
            if email_mode:
                recipient_ids_all = set(mail_values.pop('partner_ids', [])) | set(self.partner_ids.ids)
                mail_values['recipient_ids'] = [(4, pid) for pid in recipient_ids_all]

            # when having no specific reply_to -> fetch rendered email_from in mailing mode
            # and don't add anything in comment mode
            reply_to = reply_to_values.get(res_id)
            if not reply_to and email_mode:
                reply_to = mail_values.get('email_from', False)
            if reply_to:
                mail_values['reply_to'] = reply_to

            # body: render layout in email mode (comment mode is managed by the
            # notification process, see @_notify_thread_by_email)
            if email_mode and self.email_layout_xmlid and mail_values['recipient_ids']:
                lang = langs[res_id]
                recipient_ids = [command[1] for command in mail_values['recipient_ids']]
                msg_vals = {
                    'email_layout_xmlid': self.email_layout_xmlid,
                    'model': self.model,
                    'res_id': res_id,
                }
                new_mail_message_values = {'body': mail_values['body']}
                if self.template_id:
                    new_mail_message_values['email_add_signature'] = False
                message_inmem = self.env['mail.message'].new(new_mail_message_values)
                for _lang, render_values, recipients_group_data in record._notify_get_classified_recipients_iterator(
                    message_inmem,
                    [{
                        'active': True,
                        'email_normalized': False,  # not used in this flow anyway
                        'id': pid,
                        'is_follower': False,
                        'lang': lang,
                        'name': False,  # not used in this flow anyway
                        'groups': [],
                        'notif': 'email',
                        'share': True,
                        'type': 'customer',
                        'uid': False,
                        'ushare': False,
                    } for pid in recipient_ids],
                    msg_vals=msg_vals,
                    model_description=False,  # force dynamic computation
                    force_email_lang=lang,
                ):
                    mail_body = record._notify_by_email_render_layout(
                        message_inmem,
                        recipients_group_data,
                        msg_vals=msg_vals,
                        render_values=render_values,
                    )
                    mail_values['body_html'] = mail_body

        return mail_values_all