def _notify_thread_by_email(self, message, recipients_data, *, msg_vals=False,
                                mail_auto_delete=True,  # mail.mail
                                model_description=False, force_email_company=False, force_email_lang=False,  # rendering
                                force_record_name=False,  # rendering
                                subtitles=None,  # rendering
                                force_send=True, send_after_commit=True,  # email send
                                **kwargs):
        """ Method to send emails notifications linked to a message.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like a list of dicts containing information. See
          ``MailThread._notify_get_recipients()``;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries if given;

        :param bool mail_auto_delete: delete notification emails once sent;

        :param str model_description: description of current model, given to
          avoid fetching it and easing translation support;
        :param record force_email_company: <res.company> record used when rendering
          notification layout. Otherwise computed based on current record;
        :param str force_email_lang: lang used when rendering content, used
          notably to compute model name or translate access buttons;
        :param str force_record_name: record_name to use instead of being
          related record's display_name;
        :param list subtitles: optional list set as template value "subtitles";

        :param bool force_send: send emails directly instead of using queue;
        :param bool send_after_commit: if force_send, tells to send emails after
          the transaction has been committed using a post-commit hook;
        """
        partners_data = [r for r in recipients_data if r['notif'] == 'email']
        if not partners_data:
            return True

        additional_values = {'auto_delete': mail_auto_delete}
        if kwargs.get('mail_headers'):
            additional_values['headers'] = kwargs['mail_headers']
        base_mail_values = self._notify_by_email_get_base_mail_values(
            message, partners_data, additional_values=additional_values,
        )
        base_notification_values = self._notify_by_email_get_base_notification_values(message)

        # Clean the context to get rid of residual default_* keys that could cause issues during
        # the mail.mail creation.
        # Example: 'default_state' would refer to the default state of a previously created record
        # from another model that in turns triggers an assignation notification that ends up here.
        # This will lead to a traceback when trying to create a mail.mail with this state value that
        # doesn't exist.
        SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self.env.context))
        SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self.env.context))
        emails = self.env['mail.mail'].sudo()

        # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
        gen_batch_size = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')
        ) or 50  # be sure to not have 0, as otherwise no iteration is done
        notif_create_values = []
        for _lang, render_values, recipients_group in self._notify_get_classified_recipients_iterator(
            message,
            partners_data,
            msg_vals=msg_vals,
            model_description=model_description,
            force_email_company=force_email_company,
            force_email_lang=force_email_lang,
            force_record_name=force_record_name,
            subtitles=subtitles,
        ):
            # generate notification email content
            mail_body = self._notify_by_email_render_layout(
                message,
                recipients_group,
                msg_vals=msg_vals,
                render_values=render_values,
            )
            recipients_emails = recipients_group['recipients_emails']
            recipients_ids = recipients_group['recipients_ids']

            # create MailMail for partners
            for recipients_ids_chunk in split_every(gen_batch_size, recipients_ids):
                mail_values = self._notify_by_email_get_final_mail_values(
                    recipients_ids_chunk,
                    base_mail_values,
                    additional_values={'body_html': mail_body}
                )
                new_email = SafeMail.create(mail_values)

                if new_email and recipients_ids_chunk:
                    notif_create_values += [{
                        'mail_mail_id': new_email.id,
                        'res_partner_id': recipient_id,
                        **base_notification_values,
                    } for recipient_id in recipients_ids_chunk]
                emails += new_email
            # create MailMail for email-only recipients
            if recipients_emails:
                mail_values = self._notify_by_email_get_final_mail_values(
                    [], base_mail_values,
                    additional_values={'body_html': mail_body},
                )
                mail_values['email_to'] = ','.join(recipients_emails)
                new_email = SafeMail.create(mail_values)
                notif_create_values += [{
                    'mail_email_address': email,
                    'mail_mail_id': new_email.id,
                    **base_notification_values,
                } for email in recipients_emails]
                emails += new_email

        if notif_create_values:
            SafeNotification.create(notif_create_values)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        if force_send := self.env.context.get('mail_notify_force_send', force_send):
            force_send_limit = int(self.env['ir.config_parameter'].sudo().get_param('mail.mail.force.send.limit', 100))
            force_send = len(emails) < force_send_limit
        if force_send:
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if send_after_commit:
                emails.send_after_commit()
            else:
                emails.send()

        return True