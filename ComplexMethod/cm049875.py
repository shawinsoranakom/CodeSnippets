def _detect_loop_sender(self, message, message_dict, routes):
        """This method returns True if the incoming email should be ignored.

        The goal of this method is to prevent loops which can occur if an auto-replier
        send emails to Odoo.
        """
        email_from = message_dict.get('email_from')
        if not email_from:
            return False

        email_from_normalized = email_normalize(email_from)

        if self.env['mail.gateway.allowed'].sudo().search_count(
           [('email_normalized', '=', email_from_normalized)]
        ):
            return False

        # Detect the email address sent to many emails
        get_param = self.env['ir.config_parameter'].sudo().get_param
        # Period in minutes in which we will look for <mail.mail>
        LOOP_MINUTES = int(get_param('mail.gateway.loop.minutes', 120))
        LOOP_THRESHOLD = int(get_param('mail.gateway.loop.threshold', 20))

        create_date_limit = self.env.cr.now() - datetime.timedelta(minutes=LOOP_MINUTES)
        author_id = message_dict.get('author_id')

        # Search only once per model
        model_res_ids = dict()
        for model, thread_id, *__ in routes or []:
            model_res_ids.setdefault(model, list()).append(thread_id)

        for model_name, thread_ids in model_res_ids.items():
            model = self.env[model_name]
            if not hasattr(model, '_detect_loop_sender_domain'):
                continue

            loop_new, loop_update = False, False
            search_new = 0 in thread_ids  # route creating new records = thread_id = 0
            doc_ids = list(filter(None, thread_ids))  # route updating records = thread_id set

            # search records created by email -> alias creating new records
            if search_new:
                base_domain = model._detect_loop_sender_domain(email_from_normalized)
                if base_domain:
                    mail_new_count = model.sudo().search_count(
                        Domain.AND([
                            [('create_date', '>=', create_date_limit)],
                            base_domain,
                        ]),
                    )
                    loop_new = mail_new_count >= LOOP_THRESHOLD

            # search messages linked to email -> alias updating records
            if doc_ids and not loop_new:
                base_msg_domain = Domain([('model', '=', model._name), ('res_id', 'in', doc_ids), ('create_date', '>=', create_date_limit), ('message_type', '=', 'email')])
                if author_id:
                    msg_domain = Domain('author_id', '=', author_id) & base_msg_domain
                else:
                    msg_domain = Domain('email_from', 'in', [email_from, email_from_normalized]) & base_msg_domain
                mail_update_groups = self.env['mail.message'].sudo()._read_group(msg_domain, ['res_id'], ['__count'])
                if mail_update_groups:
                    loop_update = any(
                        group[1] >= LOOP_THRESHOLD
                        for group in mail_update_groups
                    )

            if loop_new or loop_update:
                if loop_new:
                    _logger.info('--> ignored mail from %s to %s with Message-Id %s: created too many <%s>',
                                message_dict.get('email_from'), message_dict.get('to'), message_dict.get('message_id'), model)
                if loop_update:
                    _logger.info('--> ignored mail from %s to %s with Message-Id %s: too much replies on same <%s>',
                                message_dict.get('email_from'), message_dict.get('to'), message_dict.get('message_id'), model)
                body = self.env['ir.qweb']._render(
                    'mail.message_notification_limit_email',
                    {'email': message_dict.get('to')},
                    minimal_qcontext=True,
                    raise_if_not_found=False,
                )
                self._routing_create_bounce_email(
                    email_from, body, message,
                    # add a reference with a tag, to be able to ignore response to this email
                    references=f'{message_dict["message_id"]} {generate_tracking_message_id("loop-detection-bounce-email")}')
                return True

        return False