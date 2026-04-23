def _call_nemhandel_proxy(self, endpoint, params=None):
        self.ensure_one()
        if self.proxy_type != 'nemhandel':
            raise UserError(_('EDI user should be of type Nemhandel'))

        errors = {
            'code_incorrect': _('The verification code is not correct'),
            'code_expired': _('This verification code has expired. Please request a new one.'),
            'too_many_attempts': _('Too many attempts to request an SMS code. Please try again later.'),
        }

        params = params or {}
        try:
            response = self._make_request(
                f"{self._get_server_url()}{endpoint}",
                params=params,
            )
        except AccountEdiProxyError as e:
            raise UserError(e.message)

        if 'error' in response:
            error_code = response['error'].get('code')
            error_message = response['error'].get('subject') or response['error'].get('data', {}).get('message')
            raise UserError(errors.get(error_code) or error_message or _('Connection error, please try again later.'))
        return response