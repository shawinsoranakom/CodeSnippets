def _make_request(self, url, params=False, *, auth_type: Literal['hmac', 'asymmetric'] = 'hmac'):
        ''' Make a request to proxy and handle the generic elements of the reponse (errors, new refresh token).
        '''
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': params or {},
            'id': uuid.uuid4().hex,
        }

        # Last barrier : in case the demo mode is not handled by the caller, we block access.
        if self.edi_mode == 'demo':
            raise AccountEdiProxyError("block_demo_mode", "Can't access the proxy in demo mode")

        try:
            res = requests.post(
                url,
                json=payload,
                timeout=DEFAULT_TIMEOUT,
                headers={'content-type': 'application/json'},
                auth=OdooEdiProxyAuth(user=self, auth_type=auth_type))
            res.raise_for_status()
            response = res.json()
        except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            _logger.warning('Connection error <%(url)s>: %(error)s', {'url': url, 'error': e})
            raise AccountEdiProxyError('connection_error',
                _('The url that this service requested returned an error. The url it tried to contact was %s', url))

        if 'error' in response:
            message = _('The url that this service requested returned an error. The url it tried to contact was %(url)s. %(error_message)s', url=url, error_message=response['error']['message'])
            if response['error']['code'] == 404:
                message = _('The url that this service tried to contact does not exist. The url was “%s”', url)
            raise AccountEdiProxyError('connection_error', message)

        proxy_error = response['result'].pop('proxy_error', False)
        if proxy_error:
            error_code = proxy_error['code']
            if error_code == 'refresh_token_expired':
                self._renew_token()
                self.env.cr.commit()  # We do not want to lose it if in the _make_request below something goes wrong
                return self._make_request(url, params, auth_type='hmac')
            if error_code == 'no_such_user':
                # This error is also raised if the user didn't exchange data and someone else claimed the edi_identificaiton.
                self.sudo().active = False
            if error_code == 'invalid_signature':
                raise AccountEdiProxyError(
                    error_code,
                    _("Failed to connect to Odoo Access Point server. This might be due to another connection to Odoo Access Point "
                      "server. It can occur if you have duplicated your database. \n\n"
                      "If you are not sure how to fix this, please contact our support."),
                )
            raise AccountEdiProxyError(error_code, proxy_error['message'] or False)

        return response['result']