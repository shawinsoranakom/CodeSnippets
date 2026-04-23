def _notify_attendees(self, mail_template, notify_author=False, force_send=False):
        """ Notify attendees about event main changes (invite, cancel, ...) based
        on template.

        :param mail_template: a mail.template record
        :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
        """
        # TDE FIXME: check this
        if force_send:
            force_send_limit = int(self.env['ir.config_parameter'].sudo().get_param('mail.mail_force_send_limit', 100))
        notified_attendees_ids = set(self.ids)
        for event, attendees in self.grouped('event_id').items():
            if event._skip_send_mail_status_update():
                notified_attendees_ids -= set(attendees.ids)
        notified_attendees = self.browse(notified_attendees_ids)
        if isinstance(mail_template, str):
            raise ValueError('Template should be a template record, not an XML ID anymore.')
        if self.env['ir.config_parameter'].sudo().get_param('calendar.block_mail') or self.env.context.get("no_mail_to_attendees"):
            return False
        if not mail_template:
            _logger.warning("No template passed to %s notification process. Skipped.", self)
            return False

        # get ics file for all meetings
        ics_files = notified_attendees.event_id._get_ics_file()

        # If the mail template has attachments, prepare copies for each attendee (to be added to each attendee's mail)
        if mail_template.attachment_ids:

            # Setting res_model to ensure attachments are linked to the msg (otherwise only internal users are allowed link attachments)
            attachments_values = [a.copy_data({'res_id': 0, 'res_model': 'mail.compose.message'})[0] for a in mail_template.attachment_ids]
            attachments_values *= len(self)
            attendee_attachment_ids = self.env['ir.attachment'].create(attachments_values).ids

            # Map attendees to their respective attachments
            template_attachment_count = len(mail_template.attachment_ids)
            attendee_id_attachment_id_map = dict(zip(self.ids, split_every(template_attachment_count, attendee_attachment_ids, list)))

        mail_messages = self.env['mail.message']
        for attendee in notified_attendees:
            if attendee.email and attendee._should_notify_attendee(notify_author=notify_author):
                event_id = attendee.event_id.id
                ics_file = ics_files.get(event_id)

                # Add template attachments copies to the attendee's email, if available
                attachment_ids = attendee_id_attachment_id_map[attendee.id] if mail_template.attachment_ids else []

                if ics_file:
                    context = {
                        **clean_context(self.env.context),
                        'no_document': True,  # An ICS file must not create a document
                    }
                    attachment_ids += self.env['ir.attachment'].with_context(context).create({
                        'datas': base64.b64encode(ics_file),
                        'description': 'invitation.ics',
                        'mimetype': 'text/calendar',
                        'res_id': 0,
                        'res_model': 'mail.compose.message',
                        'name': 'invitation.ics',
                    }).ids

                body = mail_template._render_field(
                    'body_html',
                    attendee.ids,
                    compute_lang=True)[attendee.id]
                subject = mail_template._render_field(
                    'subject',
                    attendee.ids,
                    compute_lang=True)[attendee.id]
                email_from = mail_template._render_field(
                    'email_from',
                    attendee.ids)[attendee.id]
                mail_messages += attendee.event_id.with_context(no_document=True).sudo().message_notify(
                    email_from=email_from or None,  # use None to trigger fallback sender
                    author_id=attendee.event_id.user_id.partner_id.id or self.env.user.partner_id.id,
                    body=body,
                    subject=subject,
                    notify_author=notify_author,
                    partner_ids=attendee.partner_id.ids,
                    email_layout_xmlid='mail.mail_notification_light',
                    attachment_ids=attachment_ids,
                    force_send=False,
                )
        # batch sending at the end
        if force_send and len(notified_attendees) < force_send_limit:
            mail_messages.sudo().mail_ids.send_after_commit()