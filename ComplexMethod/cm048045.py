def _l10n_in_edi_connect_to_server(self, url_end_point, json_payload=False, params=False):
        """
        url_end_point possible values (generate, getirnbydocdetails, generate_ewaybill_by_irn, get_ewaybill_by_irn, cancel)
        is used to get the EDI response from the server
        """
        company = self.company_id
        token = company._l10n_in_edi_get_token()
        if not token:
            return {
                'error': [{
                    'code': '0',
                    'message': _(
                        "Ensure GST Number set on company setting and API are Verified."
                    )
                }]
            }
        default_params = {
            'auth_token': token,
            'username': company.sudo().l10n_in_edi_username,
            'gstin': company.vat,
        }
        if params:
            # To be used when generate_ewaybill_by_irn, get_ewaybill_by_irn
            params.update(default_params)
        else:
            params = {
                **default_params,
                'json_payload': json_payload
            }
        try:
            response = self.env['iap.account']._l10n_in_connect_to_server(
                company.sudo().l10n_in_edi_production_env,
                params,
                f"/iap/l10n_in_edi/1/{url_end_point}",
                'l10n_in_edi.endpoint'
            )
        except AccessError as e:
            _logger.warning("Connection error: %s", e.args[0])
            return {
                'error': [{
                    'code': '404',
                    'message': _(
                        "Unable to connect to the online E-invoice service."
                        "The web service may be temporary down. Please try again in a moment."
                    )
                }]
            }
        if (error := response.get('error')) and '1005' in [e.get("code") for e in error]:
            # Invalid token error then create new token and send generate request again.
            # This happen when authenticate called from another odoo instance with same credentials (like. Demo/Test)
            authenticate_response = company._l10n_in_edi_authenticate()
            if not authenticate_response.get("error"):
                response = self._l10n_in_edi_connect_to_server(
                    url_end_point=url_end_point,
                    json_payload=json_payload,
                    params=params
                )
            else:
                return authenticate_response
        return response