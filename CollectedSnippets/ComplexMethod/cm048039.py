def _l10n_in_edi_send_invoice(self):
        self.ensure_one()
        if self.l10n_in_edi_error:
            # make sure to clear the error before sending again
            self.l10n_in_edi_error = False
            self.message_post(body=_(
                "Retrying to send your E-Invoice to government portal."
            ))
        partners = set(self._get_l10n_in_seller_buyer_party().values())
        for partner in partners:
            if partner_validation := partner._l10n_in_edi_strict_error_validation():
                self.l10n_in_edi_error = Markup("<br>").join(partner_validation)
                return {'messages': partner_validation}
        self._l10n_in_lock_invoice()
        generate_json = self._l10n_in_edi_generate_invoice_json()
        response = self._l10n_in_edi_connect_to_server(
            url_end_point='generate',
            json_payload=generate_json
        )
        if error := response.get('error', {}):
            odoobot_id = self.env.ref('base.partner_root').id
            error_codes = [e.get("code") for e in error]
            if '2150' in error_codes:
                # Get IRN by details in case of IRN is already generated
                # this happens when timeout from the Government portal but IRN is generated
                response = self._l10n_in_edi_connect_to_server(
                    url_end_point='getirnbydocdetails',
                    params={
                        "doc_type": (
                            (self.move_type == "out_refund" and "CRN")
                            or (self.debit_origin_id and "DBN")
                            or "INV"
                        ),
                        "doc_num": self.name,
                        "doc_date": self.invoice_date and self.invoice_date.strftime("%d/%m/%Y"),
                    }
                )
                mismatch_error = []
                decoded_response = {}
                if jwt:
                    try:
                        if data := response.get('data'):
                            signinvoice = data['SignedInvoice']
                            decoded_response = jwt.decode(signinvoice, options={'verify_signature': False})
                            decoded_response = json.loads(decoded_response['data'])
                    except (json.JSONDecodeError, jwt.exceptions.DecodeError) as e:
                        _logger.warning("Failed to decode SignedInvoice JWT payload: %s", str(e))
                if decoded_response:
                    received_gstin = decoded_response['BuyerDtls']['Gstin']
                    expected_gstin = generate_json['BuyerDtls']['GSTIN']
                    received_total_invoice_value = decoded_response['ValDtls']['TotInvVal']
                    expected_total_invoice_value = generate_json['ValDtls']['TotInvVal']
                    # Check for mismatch between decoded and expected e-invoice details:
                    # - Buyer GSTIN must match
                    # - Total Invoice Value must be within the allowed government tolerance range:
                    #   For example, if the expected invoice value is 100,
                    #   the valid range is from 99 (value - 1) to 101 (value + 1),
                    #   i.e., 99.00 < received value < 101.00
                    if (received_gstin != expected_gstin or
                        not expected_total_invoice_value - 1 < received_total_invoice_value < expected_total_invoice_value + 1
                    ):
                        mismatch_error = [{
                            'code': '2150',
                            'message': _("Duplicate IRN found for this invoice, but the buyer details or invoice values do not match.")
                        }]
                # Handle the result based on mismatch or response error
                if mismatch_error:
                    error = mismatch_error
                elif not response.get("error"):
                    error = []
                    link = Markup(
                        "<a href='https://einvoice1.gst.gov.in/Others/VSignedInvoice'>%s</a>"
                    ) % (_("here"))
                    self.message_post(
                        author_id=odoobot_id,
                        body=_(
                            "Somehow this invoice has been submited to government before."
                            "%(br)sNormally, this should not happen too often"
                            "%(br)sJust verify value of invoice by upload json to government website %(link)s.",
                            br=Markup("<br/>"),
                            link=link
                        )
                    )
            if (no_credit := 'no-credit' in error_codes) or error:
                msg = Markup("<br/>").join(
                    ["[%s] %s" % (e.get("code"), e.get("message")) for e in error]
                )
                is_warning = any(warning_code in error_codes for warning_code in ('404', 'timeout'))
                self.l10n_in_edi_error = (
                    self._l10n_in_edi_get_iap_buy_credits_message()
                    if no_credit else msg
                )
                # avoid return `l10n_in_edi_error` because as a html field
                # values are sanitized with `<p>` tag
                return {
                    'messages': [msg],
                    'is_warning': is_warning
                }
        data = response.get("data", {})
        json_dump = json.dumps(data)
        json_name = "%s_einvoice.json" % (self.name.replace("/", "_"))
        attachment = self.env["ir.attachment"].create({
            'name': json_name,
            'raw': json_dump.encode(),
            'res_model': self._name,
            'res_field': 'l10n_in_edi_attachment_file',
            'res_id': self.id,
            'mimetype': 'application/json',
            'company_id': self.company_id.id,
        })
        request_json_dump = json.dumps(generate_json, indent=4)
        request_json_name = "%s_request.json" % (self.name.replace("/", "_"))
        request_attachment = self.env["ir.attachment"].create({
            'name': request_json_name,
            'raw': request_json_dump.encode(),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/json',
            'company_id': self.company_id.id,
        })
        self.l10n_in_edi_status = 'sent'
        message = []
        for partner in partners:
            if partner_validation := self._l10n_in_edi_optional_field_validation(partner):
                message.append(
                    Markup("<strong><em>%s</em></strong><br>%s") % (partner.name, Markup("<br>").join(partner_validation))
                )
        message.append(self.env._("E-invoice submitted successfully."))
        if message:
            self.message_post(
                attachment_ids=[request_attachment.id, attachment.id],
                body=Markup("<strong>%s</strong><br>%s") % (_("Following:"), Markup("<br>").join(message))
            )