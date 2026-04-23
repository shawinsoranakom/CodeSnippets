def _l10n_sa_call_api(self, request_data, request_url, method):
        """
            Helper function to make api calls to the ZATCA API Endpoint
        """
        api_url = ZATCA_API_URLS[self.company_id.l10n_sa_api_mode]
        request_url = urljoin(api_url, request_url)
        status_code = False
        try:
            request_response = requests.request(method, request_url, data=request_data.get('body'),
                                                headers={
                                                    **self._l10n_sa_api_headers(),
                                                    **request_data.get('header')
                                                }, timeout=30)
            request_response.raise_for_status()
        except (ValueError, HTTPError) as ex:
            # The 400 case means that it is rejected by ZATCA, but we need to update the hash as done for accepted.
            # In the 401+ cases, it is like the server is overloaded e.g. and we still need to resend later.  We do not
            # erase the index chain (excepted) because for ZATCA, one ICV (index chain) needs to correspond to one invoice.
            if (status_code := ex.response.status_code) not in {400, 409}:
                return {
                    'error': (Markup("<b>[%s]</b>") % status_code) + _("Server returned an unexpected error: %(error)s",
                               error=(request_response.text or str(ex))),
                    'blocking_level': 'warning',
                    'status_code': status_code,
                    'excepted': True,
                }
        except RequestException as ex:
            # Usually only happens if a Timeout occurs. In this case we're not sure if the invoice was accepted or
            # rejected, or if it even made it to ZATCA
            return {'error': str(ex), 'blocking_level': 'warning', 'excepted': True}

        if request_response.status_code == '303':
            return {'error': _('Clearance and reporting seem to have been mixed up. '),
                    'blocking_level': 'warning', 'excepted': True}

        try:
            response_data = request_response.json()
        except json.decoder.JSONDecodeError:
            return {
                'error': _("JSON response from ZATCA could not be decoded"),
                'blocking_level': 'error'
            }
        response_data['status_code'] = request_response.status_code

        if status_code == 409:
            return response_data

        val_res = response_data.get('validationResults', {})
        if not request_response.ok and (val_res.get('errorMessages') or val_res.get('warningMessages')):
            error = "" if not status_code else Markup("<b>[%s]</b>") % (status_code)
            if isinstance(response_data, dict) and val_res.get('errorMessages'):
                error += _("Invoice submission to ZATCA returned errors")
                return {
                    'error': error,
                    'json_errors': response_data,
                    'blocking_level': 'error',
                }
            error += request_response.reason
            return {
                'error': error,
                'blocking_level': 'error',
            }
        return response_data