def mailing_send_feedback(self, mailing_id=None, document_id=None,
                              email=None, hash_token=None,
                              last_action=None,
                              opt_out_reason_id=False, feedback=None,
                              **post):
        """ Feedback can be given after some actions, notably after opt-outing
        from mailing lists or adding an email in the blocklist.

        This controller tries to write the customer feedback in the most relevant
        record. Feedback consists in two parts, the opt-out reason (based on data
        in 'mailing.subscription.optout' model) and the feedback itself (which
        is triggered by the optout reason 'is_feedback' fields).
        """
        email_found, hash_token_found = self._fetch_user_information(email, hash_token)
        try:
            mailing_sudo = self._check_mailing_email_token(
                mailing_id, document_id, email_found, hash_token_found,
                required_mailing_id=False,
            )
        except BadRequest:
            return 'error'
        except (NotFound, Unauthorized):
            return 'unauthorized'

        if not opt_out_reason_id:
            return 'error'
        feedback = feedback.strip() if feedback else ''
        message = ''
        if feedback:
            if not request.env.user._is_public():
                author_name = f'{request.env.user.name} ({email_found})'
            else:
                author_name = email_found
            message = Markup("<p>%s<br />%s</p>") % (
                _('Feedback from %(author_name)s', author_name=author_name),
                feedback
            )

        # blocklist addition: opt-out and feedback linked to the mail.blacklist records
        if last_action == 'blocklist_add':
            mail_blocklist = self._fetch_blocklist_record(email)
            if mail_blocklist:
                if message:
                    mail_blocklist._track_set_log_message(message)
                mail_blocklist.opt_out_reason_id = opt_out_reason_id

        # opt-outed from mailing lists (either from a mailing or directly from 'my')
        # -> in that case, update recently-updated subscription records and log on
        # contacts
        documents_for_post = []
        if (last_action in {'subscription_updated', 'subscription_updated_optout'} or
            (not last_action and (not mailing_sudo or mailing_sudo.mailing_on_mailing_list))):
            contacts = self._fetch_contacts(email_found)
            contacts.subscription_ids.filtered(
                lambda sub: sub.opt_out and sub.opt_out_datetime >= (fields.Datetime.now() - timedelta(minutes=10))
            ).opt_out_reason_id = opt_out_reason_id
            if message:
                documents_for_post = contacts
        # feedback coming from a mailing, without additional context information: log
        elif mailing_sudo and message:
            documents_for_post = request.env[mailing_sudo.mailing_model_real].sudo().search(
                [('id', '=', document_id)
            ])

        for document_sudo in documents_for_post:
            document_sudo.message_post(body=message)

        return True