def _ewaybill_make_transaction(self, operation_type, json_payload):
        """
        :params operation_type: operation_type must be strictly `generate` or `cancel`
        :params json_payload: to be sent as params
        This method handles the common errors in generating and canceling the ewaybill
        """
        try:
            if not self._ewaybill_check_authentication():
                self._raise_ewaybill_no_config_error()
            params = {"json_payload": json_payload}
            url_path = f"/iap/l10n_in_edi_ewaybill/1/{operation_type}"
            response = self._ewaybill_jsonrpc_to_server(
                url_path=url_path,
                params=params
            )
            return response
        except EWayBillError as e:
            if "no-credit" in e.error_codes:
                e.error_json['odoo_warning'].append({
                    'message': self.env['account.move']._l10n_in_edi_get_iap_buy_credits_message()
                })
                raise

            if '238' in e.error_codes:
                # Invalid token eror then create new token and send generate request again.
                # This happens when authenticate called from another odoo instance with same credentials
                # (like. Demo/Test)
                with contextlib.suppress(EWayBillError):
                    self._ewaybill_authenticate()
                return self._ewaybill_jsonrpc_to_server(
                    url_path=url_path,
                    params=params,
                )

            if operation_type == "cancel" and "312" in e.error_codes:
                # E-waybill is already canceled
                # this happens when timeout from the Government portal but IRN is generated
                # Avoid raising error in this case, since it is already cancelled
                response = e.error_json
                response['odoo_warning'].append({
                    'message': Markup("%s<br/>%s:<br/>%s") % (
                        self.env['l10n.in.ewaybill']._get_default_help_message(
                            self.env._('cancelled')
                        ),
                        _("Error"),
                        e.get_all_error_message()
                    ),
                    'message_post': True
                })
                # We return the error json as this a government document
                # On which in case of error 312, consider the ewaybill
                # as already cancelled
                return response

            if operation_type == "generate" and "604" in e.error_codes:
                # Get E-waybill by details in case of E-waybill is already generated
                # this happens when timeout from the Government portal but E-waybill is generated
                response = self._ewaybill_get_by_consigner(
                    document_type=json_payload.get("docType"),
                    document_number=json_payload.get("docNo")
                )
                return response
            raise