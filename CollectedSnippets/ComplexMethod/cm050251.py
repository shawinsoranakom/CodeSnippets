def _l10n_id_coretax_build_invoice_vals(self, vals):
        """ Fill in vals with invoice-related information """
        self.ensure_one()

        partner = self.commercial_partner_id
        trx_code = self.l10n_id_kode_transaksi

        l10n_id_buyer_document_type_mapping_to_xml = {
            'TIN': 'TIN',
            'NIK': 'National ID',
            'Passport': 'Passport',
            'Other': 'Other ID'
        }

        vals.update({
            "TIN": self.company_id.vat,
            "TaxInvoiceDate": self.invoice_date.strftime("%Y-%m-%d"),
            "TaxInvoiceOpt": "Normal",
            "TrxCode": trx_code,
            "AddInfo": "",
            "CustomDoc": self.l10n_id_coretax_custom_doc or "",
            "CustomDocMonthYear": self.l10n_id_coretax_custom_doc_month_year and self.l10n_id_coretax_custom_doc_month_year.strftime("%m%Y") or "",
            "FacilityStamp": "",
            "RefDesc": self.name,
            "SellerIDTKU": self.company_id.vat + (self.company_id.partner_id.l10n_id_tku or '000000'),
            "BuyerDocument": l10n_id_buyer_document_type_mapping_to_xml.get(partner.l10n_id_buyer_document_type, partner.l10n_id_buyer_document_type),
            "BuyerTin": partner.vat if partner.l10n_id_buyer_document_type == "TIN" else "0000000000000000",
            "BuyerCountry": COUNTRY_CODE_MAP.get(partner.country_id.code),
            "BuyerDocumentNumber": partner.l10n_id_buyer_document_number if partner.l10n_id_buyer_document_type != "TIN" else "",
            "BuyerName": self.partner_id.name,
            "BuyerAdress": self.partner_id.contact_address.replace('\n', ' ').strip(),
            "BuyerEmail": partner.email or "",
            "BuyerIDTKU": partner.vat + (partner.l10n_id_tku or '000000'),
        })

        if trx_code == '07':
            vals['AddInfo'] = self.l10n_id_coretax_add_info_07
            vals['FacilityStamp'] = self.l10n_id_coretax_facility_info_07
        elif trx_code == '08':
            vals['AddInfo'] = self.l10n_id_coretax_add_info_08
            vals['FacilityStamp'] = self.l10n_id_coretax_facility_info_08