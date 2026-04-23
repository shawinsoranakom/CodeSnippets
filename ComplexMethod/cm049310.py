def open_microsoft_outlook_uri(self):
        """Open the URL to accept the Outlook permission.

        This is done with an action, so we can force the user the save the form.
        We need him to save the form so the current mail server record exist in DB and
        we can include the record ID in the URL.
        """
        self.ensure_one()

        if not self.env.is_admin():
            raise AccessError(_('Only the administrator can link an Outlook mail server.'))

        email_normalized = email_normalize(self[self._email_field])

        if not email_normalized:
            raise UserError(_('Please enter a valid email address.'))

        Config = self.env['ir.config_parameter'].sudo()
        microsoft_outlook_client_id = Config.get_param('microsoft_outlook_client_id')
        microsoft_outlook_client_secret = Config.get_param('microsoft_outlook_client_secret')
        is_configured = microsoft_outlook_client_id and microsoft_outlook_client_secret

        if not is_configured:  # use IAP (see '/microsoft_outlook/iap_confirm')
            if release.version_info[-1] != 'e':
                raise UserError(_('Please configure your Outlook credentials.'))

            outlook_iap_endpoint = self.env['ir.config_parameter'].sudo().get_param(
                'mail.server.outlook.iap.endpoint',
                self._DEFAULT_OUTLOOK_IAP_ENDPOINT,
            )
            db_uuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')

            # final callback URL that will receive the token from IAP
            callback_params = url_encode({
                'model': self._name,
                'rec_id': self.id,
                'csrf_token': self._get_outlook_csrf_token(),
            })
            callback_url = url_join(self.get_base_url(), f'/microsoft_outlook/iap_confirm?{callback_params}')

            try:
                response = requests.get(
                    url_join(outlook_iap_endpoint, '/api/mail_oauth/1/outlook'),
                    params={'db_uuid': db_uuid, 'callback_url': callback_url},
                    timeout=OUTLOOK_TOKEN_REQUEST_TIMEOUT)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                _logger.error('Can not contact IAP: %s.', e)
                raise UserError(_('Oops, we could not authenticate you. Please try again later.'))

            response = response.json()
            if 'error' in response:
                self._raise_iap_error(response['error'])

            # URL on IAP that will redirect to Outlook login page
            microsoft_outlook_uri = response['url']

        else:
            microsoft_outlook_uri = self.microsoft_outlook_uri

        if not microsoft_outlook_uri:
            raise UserError(_('Please configure your Outlook credentials.'))

        return {
            'type': 'ir.actions.act_url',
            'url': microsoft_outlook_uri,
            'target': 'self',
        }