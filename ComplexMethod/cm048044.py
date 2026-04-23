def _l10n_in_edi_generate_invoice_json(self):
        self.ensure_one()
        tax_details = self._l10n_in_prepare_tax_details()
        seller_buyer = self._get_l10n_in_seller_buyer_party()
        tax_details_by_code = self._get_l10n_in_tax_details_by_line_code(tax_details['tax_details'])
        is_intra_state = self.l10n_in_state_id == self.company_id.state_id
        is_overseas = self.l10n_in_gst_treatment == "overseas"
        line_ids = []
        global_discount_line_ids = []
        grouping_lines = self.invoice_line_ids.grouped(
            lambda l: l.display_type == 'product' and (l._l10n_in_is_global_discount() and 'global_discount' or 'lines')
        )
        default_line = self.env['account.move.line'].browse()
        lines = grouping_lines.get('lines', default_line)
        global_discount_line = grouping_lines.get('global_discount', default_line)
        tax_details_per_record = tax_details['tax_details_per_record']
        sign = self.is_inbound() and -1 or 1
        rounding_amount = sum(line.balance for line in self.line_ids if line.display_type == 'rounding') * sign
        global_discount_amount = sum(line.balance for line in global_discount_line) * -sign
        in_round = self._l10n_in_round_value
        json_payload = {
            "Version": "1.1",
            "TranDtls": {
                "TaxSch": "GST",
                "SupTyp": self._l10n_in_get_supply_type(tax_details_by_code.get('igst_amount')),
                "RegRev": tax_details_by_code.get('is_reverse_charge') and "Y" or "N",
                "IgstOnIntra": (
                    # for Export SEZ LUT tax as per e-invoice api doc validation point 32
                    # Export and SEZ must be treated as Inter state supply
                    self.l10n_in_gst_treatment not in ('special_economic_zone', 'overseas')
                    and is_intra_state
                    and tax_details_by_code.get("igst_amount")
                    and "Y" or "N"
                ),
            },
            "DocDtls": {
                "Typ": (self.move_type == "out_refund" and "CRN") or (self.debit_origin_id and "DBN") or "INV",
                "No": self.name,
                "Dt": self.invoice_date and self.invoice_date.strftime("%d/%m/%Y")
            },
            "SellerDtls": self._get_l10n_in_edi_partner_details(seller_buyer['seller_details']),
            "BuyerDtls": self._get_l10n_in_edi_partner_details(
                seller_buyer['buyer_details'],
                pos_state_id=self.l10n_in_state_id,
                is_overseas=is_overseas
            ),
            "ItemList": [
                self._get_l10n_in_edi_line_details(
                    index,
                    line,
                    tax_details_per_record.get(line, {})
                )
                for index, line in enumerate(lines, start=1)
            ],
            "ValDtls": {
                "AssVal": in_round(tax_details['base_amount']),
                "CgstVal": in_round(tax_details_by_code.get("cgst_amount", 0.00)),
                "SgstVal": in_round(tax_details_by_code.get("sgst_amount", 0.00)),
                "IgstVal": in_round(tax_details_by_code.get("igst_amount", 0.00)),
                "CesVal": in_round((
                    tax_details_by_code.get("cess_amount", 0.00)
                    + tax_details_by_code.get("cess_non_advol_amount", 0.00)),
                ),
                "StCesVal": in_round((
                    tax_details_by_code.get("state_cess_amount", 0.00)
                    + tax_details_by_code.get("state_cess_non_advol_amount", 0.00)), # clean this up =p
                ),
                "Discount": in_round(global_discount_amount),
                "RndOffAmt": in_round(rounding_amount),
                "TotInvVal": in_round(
                    tax_details["base_amount"]
                    + tax_details["tax_amount"]
                    + rounding_amount
                    - global_discount_amount
                ),
            },
        }
        if self.company_currency_id != self.currency_id:
            json_payload["ValDtls"].update({
                "TotInvValFc": in_round(
                    (tax_details.get("base_amount_currency") + tax_details.get("tax_amount_currency")))
            })
        if seller_buyer['seller_details'] != seller_buyer['dispatch_details']:
            json_payload['DispDtls'] = self._get_l10n_in_edi_partner_details(
                seller_buyer['dispatch_details'],
                set_vat=False,
                set_phone_and_email=False
            )
        if seller_buyer['buyer_details'] != seller_buyer['ship_to_details']:
            json_payload['ShipDtls'] = self._get_l10n_in_edi_partner_details(
                seller_buyer['ship_to_details'],
                is_overseas=is_overseas
            )
        if is_overseas:
            json_payload['ExpDtls'] = {
                'RefClm': tax_details_by_code.get('igst_amount') and 'Y' or 'N',
                'ForCur': self.currency_id.name,
                'CntCode': seller_buyer['buyer_details'].country_id.code or '',
            }
            if shipping_bill_no := self.l10n_in_shipping_bill_number:
                json_payload['ExpDtls']['ShipBNo'] = shipping_bill_no
            if shipping_bill_date := self.l10n_in_shipping_bill_date:
                json_payload['ExpDtls']['ShipBDt'] = shipping_bill_date.strftime("%d/%m/%Y")
            if shipping_port_code_id := self.l10n_in_shipping_port_code_id:
                json_payload['ExpDtls']['Port'] = shipping_port_code_id.code
            json_valdtls = json_payload['ValDtls']
            base_and_tax_amount = tax_details.get("base_amount") + tax_details.get("tax_amount")
            # For Export If with payment of Tax then we need to include Tax in Total Invoice Value
            if json_payload['TranDtls']['SupTyp'] == 'EXPWP' and json_valdtls['AssVal'] == base_and_tax_amount:
                json_payload["ValDtls"]["TotInvVal"] = self._l10n_in_round_value(sum([
                    json_valdtls['TotInvVal'],
                    json_valdtls['IgstVal'],
                    json_valdtls['CgstVal'],
                    json_valdtls['SgstVal'],
                    json_valdtls['CesVal'],
                    json_valdtls['StCesVal'],
                ]))
                for line in json_payload["ItemList"]:
                    line["TotItemVal"] = self._l10n_in_round_value(sum([
                        line["TotItemVal"],
                        line["IgstAmt"],
                        line["CgstAmt"],
                        line["SgstAmt"],
                        line["CesAmt"],
                        line["CesNonAdvlAmt"],
                        line["StateCesAmt"],
                        line["StateCesNonAdvlAmt"],
                    ]))
        return self._l10n_in_edi_generate_invoice_json_managing_negative_lines(json_payload)