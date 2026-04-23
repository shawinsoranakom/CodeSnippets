def _prepare_outgoing_list(self, mail_server=False, doc_to_followers=None):
        """ Update mailing specific links to replace generic unsubscribe and
        view links by email-specific links. Also add headers to allow
        unsubscribe from email managers. """
        email_list = super()._prepare_outgoing_list(mail_server=mail_server, doc_to_followers=doc_to_followers)
        if not self.res_id or not self.mailing_id:
            return email_list

        base_url = self.mailing_id.get_base_url()
        for email_values in email_list:
            if not email_values['email_to']:
                continue

            # prepare links with normalize email
            email_normalized = tools.email_normalize(email_values['email_to'][0], strict=False)
            email_to = email_normalized or email_values['email_to'][0]

            unsubscribe_url = self.mailing_id._get_unsubscribe_url(email_to, self.res_id)
            unsubscribe_oneclick_url = self.mailing_id._get_unsubscribe_oneclick_url(email_to, self.res_id)
            view_url = self.mailing_id._get_view_url(email_to, self.res_id)

            # replace links in body
            if not tools.is_html_empty(email_values['body']):
                # replace generic link by recipient-specific one, except if we know
                # by advance it won't work (i.e. testing mailing scenario)
                if f'{base_url}/unsubscribe_from_list' in email_values['body'] and not self.env.context.get('mailing_test_mail'):
                    email_values['body'] = email_values['body'].replace(
                        f'{base_url}/unsubscribe_from_list',
                        unsubscribe_url,
                    )
                if f'{base_url}/view' in email_values['body']:
                    email_values['body'] = email_values['body'].replace(
                        f'{base_url}/view',
                        view_url,
                    )

            # add headers
            email_values['headers'].update({
                'List-Unsubscribe': f'<{unsubscribe_oneclick_url}>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
                'Precedence': 'list',
                'X-Auto-Response-Suppress': 'OOF',  # avoid out-of-office replies from MS Exchange
            })
        return email_list