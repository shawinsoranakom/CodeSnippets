def _l10n_in_edi_cancel_invoice(self):
        if self.l10n_in_edi_error:
            # make sure to clear the error before cancelling again
            self.l10n_in_edi_error = False
            self.message_post(body=_(
                "Retrying to send cancellation request for E-Invoice to government portal."
            ))
        self._l10n_in_lock_invoice()
        l10n_in_edi_response_json = self._get_l10n_in_edi_response_json()
        cancel_json = {
            "Irn": l10n_in_edi_response_json.get("Irn"),
            "CnlRsn": self.l10n_in_edi_cancel_reason,
            "CnlRem": self.l10n_in_edi_cancel_remarks,
        }
        response = self._l10n_in_edi_connect_to_server(url_end_point='cancel', json_payload=cancel_json)
        # Creating a lambda function so it fetches the odoobot id only when needed
        _get_odoobot_id = (
            lambda self: self.env.ref('base.partner_root').id
        )
        if error := response.get('error'):
            error_codes = [e.get('code') for e in error]
            if '9999' in error_codes:
                response = {}
                error = []
                link = Markup(
                    "<a href='https://einvoice1.gst.gov.in/Others/VSignedInvoice'>%s</a>"
                ) % (_("here"))
                self.message_post(
                    author_id=_get_odoobot_id(self),
                    body=_(
                        "Somehow this invoice had been cancelled to government before."
                        "%(br)sNormally, this should not happen too often"
                        "%(br)sJust verify by logging into government website %(link)s",
                        br=Markup("<br/>"),
                        link=link
                    )
                )
            if "no-credit" in error_codes:
                self.l10n_in_edi_error = self._l10n_in_edi_get_iap_buy_credits_message()
                return
            if error:
                self.l10n_in_edi_error = (
                    Markup("<br/>").join(
                        ["[%s] %s" % (e.get("code"), e.get("message")) for e in error]
                    )
                )
        if "error" not in response:
            json_dump = json.dumps(response.get('data', {}))
            json_name = "%s_cancel_einvoice.json" % (self.name.replace("/", "_"))
            if json_dump:
                attachment = self.env['ir.attachment'].create({
                    'name': json_name,
                    'raw': json_dump.encode(),
                    'res_model': self._name,
                    'res_field': 'l10n_in_edi_attachment_file',
                    'res_id': self.id,
                    'mimetype': 'application/json',
                })
            request_json_dump = json.dumps(cancel_json, indent=4)
            request_json_name = "%s_cancel_request.json" % (self.name.replace("/", "_"))
            request_attachment = self.env['ir.attachment'].create({
                'name': request_json_name,
                'raw': request_json_dump.encode(),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/json',
            })
            self.message_post(author_id=_get_odoobot_id(self), body=_(
                "E-Invoice has been cancelled successfully. "
                "Cancellation Reason: %(reason)s and Cancellation Remark: %(remark)s",
                reason=EDI_CANCEL_REASON[self.l10n_in_edi_cancel_reason],
                remark=self.l10n_in_edi_cancel_remarks
            ), attachment_ids=[request_attachment.id, attachment.id] if attachment else [request_attachment.id])
            self.l10n_in_edi_status = 'cancelled'
            self.button_cancel()
        if self._can_commit():
            self.env.cr.commit()
        return True