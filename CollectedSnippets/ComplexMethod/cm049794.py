def _personalize_outgoing_body(self, body, partner=False, doc_to_followers=None):
        """ Return a modified body based on the recipient (partner).

        It must be called when using standard notification layouts
        even for message without partners.

        :param str body: body to personalize for the recipient
        :param partner: <res.partner> recipient
        :param dict doc_to_followers: see ``Followers._get_mail_doc_to_followers()``
        """
        self.ensure_one()
        if (partner and self.model and self.id and  # document based only
            (getattr(self.env[self.model], '_partner_unfollow_enabled', False) or not partner.partner_share) and  # internal or model-allowance
            (doc_to_followers or {}).get((self.model, self.res_id))):
            unfollow_url = self.env['mail.thread']._notify_get_action_link(
                'unfollow', model=self.model, res_id=self.res_id, pid=partner.id)
            body = body.replace('/mail/unfollow', unfollow_url)
        else:
            body = re.sub(_UNFOLLOW_REGEX, '', body)
        return body