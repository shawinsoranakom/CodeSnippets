def _ewaybill_generate_by_irn(self, json_payload):
        self.ensure_one()
        if not self.company_id._l10n_in_edi_get_token():
            raise EWayBillError({
                'error': [{
                    'code': '0',
                    'message': self.env._(
                        "Unable to send E-waybill by IRN."
                        "Ensure GST Number set on company setting and EDI and Ewaybilll"
                        " credentials are Verified."
                    )
                }]
            })
        response = self.account_move_id._l10n_in_edi_connect_to_server(
            url_end_point='generate_ewaybill_by_irn',
            json_payload=json_payload
        )
        if response.get('error'):
            error_codes = [error.get('code') for error in response.get('error')]
            if 'no-credit' in error_codes:
                response['odoo_warning'].append({
                    'message': self.env['account.move']._l10n_in_edi_get_iap_buy_credits_message()
                })
            if '4002' in error_codes or '4026' in error_codes:
                # Get E-waybill by details in case of IRN is already generated
                # this happens when timeout from the Government portal but E-waybill is generated
                response = self.account_move_id._l10n_in_edi_connect_to_server(
                    url_end_point='get_ewaybill_by_irn',
                    params={"irn": self._get_edi_irn_number()}
                )
                response.update({
                    'odoo_warning': [{
                        'message': self._get_default_help_message(self.env._('generated')),
                        'message_post': True
                    }]
                })
            if response.get('error'):
                raise EWayBillError(response)
        return response