def _l10n_tw_edi_generate_invoice_json(self):
        self.ensure_one()
        self._l10n_tw_edi_check_before_generate_invoice_json()
        tax_type, special_tax_type, is_zero_tax_rate = self._l10n_tw_edi_determine_tax_types()
        self.l10n_tw_edi_related_number = base64.urlsafe_b64encode(uuid.uuid4().bytes)[:20]
        formatted_phone = self._reformat_phone_number(self.partner_id.phone) if self.partner_id.phone else ""
        product_lines = self.invoice_line_ids.filtered(lambda line: line.display_type == "product")
        vat = "1" if product_lines[0].tax_ids and product_lines[0].tax_ids[0].price_include else "0"

        json_data = {
            "MerchantID": self.company_id.sudo().l10n_tw_edi_ecpay_merchant_id,
            "RelateNumber": self.l10n_tw_edi_related_number,
            "CustomerIdentifier": self.partner_id.vat if self.l10n_tw_edi_is_b2b and self.partner_id.vat else "",
            "CustomerAddr": self.partner_id._l10n_tw_edi_formatted_address(),
            "CustomerEmail": self.partner_id.email or "",
            "CustomerPhone": formatted_phone,
            "InvType": self.l10n_tw_edi_invoice_type,
            "TaxType": tax_type,
        }

        if self.ref:
            json_data["InvoiceRemark"] = self.ref
        if special_tax_type:
            json_data["SpecialTaxType"] = special_tax_type

        self._l10n_tw_edi_prepare_item_list(json_data)

        if self.l10n_tw_edi_is_b2b:
            json_data["TotalAmount"] = json_data["SalesAmount"] + json_data["TaxAmount"]
        else:
            json_data.update({
                "CustomerName": self.partner_id.name,
                "Print": "1" if self.l10n_tw_edi_is_print or self.l10n_tw_edi_is_b2b else "0",
                "Donation": "1" if self.l10n_tw_edi_love_code else "0",
                "LoveCode": self.l10n_tw_edi_love_code or "",
                "CarrierType": self.l10n_tw_edi_carrier_type or "",
                "CarrierNum": self.l10n_tw_edi_carrier_number if self.l10n_tw_edi_carrier_type in ["2", "3", "4", "5"] else "",
                "CarrierNum2": self.l10n_tw_edi_carrier_number_2 if self.l10n_tw_edi_carrier_type in ["4", "5"] else "",
                "vat": vat,
            })

        if is_zero_tax_rate:
            json_data["ClearanceMark"] = self.l10n_tw_edi_clearance_mark
            json_data["ZeroTaxRateReason"] = self.l10n_tw_edi_zero_tax_rate_reason

        return json_data