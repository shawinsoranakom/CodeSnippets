def _execute_dpopay_api_request(self, payload, endpoint):
        self.ensure_one()
        if endpoint not in ('start-transaction', 'get-result', 'get-status', 'cancel-transaction'):
            raise UserError(_('Invalid endpoint'))

        mode = 'Test' if self.dpopay_test_mode else 'Production'
        url = f'{self._get_dpopay_base_url()}/{endpoint}'
        try:
            def _send_request(token_expired=False):
                headers = self._dpopay_headers(token_expired)
                _logger.info('Sending request to %s | Mode: %s | Headers: %s | Source ID: %s', url, mode, list(headers.keys()), payload.get('sourceId'))
                response = requests.post(url, json=payload, headers=headers, timeout=DPOPAY_DEFAULT_TIMEOUT)
                response_json = response.json()
                return response, response_json

            response, response_json = _send_request()
            errorCode = response_json.get('error_code') or response_json.get('resultCode')
            # Refresh Token and Retry the request if the token is expired (999912) or invalid (999913)
            if response.status_code == 401 and errorCode in ('999912', '999913'):
                _logger.info('Token expired or invalid — regenerating token...')
                response, response_json = _send_request(token_expired=True)

            response.raise_for_status()
            return response_json

        except HTTPError as error:
            _logger.warning('HTTPError: %s | Mode: %s | Source ID: %s', error, mode, payload.get('sourceId'))
            error_json = error.response.json()
            error_code = str(error_json.get('error_code') or error_json.get('errorCode') or error_json.get('resultCode'))
            error_message = error_json.get('errorMessage') or error_json.get('error_description') or error_json.get('resultDescription') or str(error_json)

            if error_code == "403":
                error_message = _("Please ensure the device is online and confirm that the Merchant ID (MID) and Terminal ID (TID) are correct. %s", error_message)

            if error_code == "999911":
                error_message = _("Invalid Chain ID. Please verify the configuration. %s", error_message)

            return {'errorMessage': error_message}

        except RequestException as error:
            _logger.warning('%s: %s | Mode: %s | Source ID: %s', error.__class__.__name__, error, mode, payload.get('sourceId'))
            return {'errorMessage': str(error)}