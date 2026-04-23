def _export_myinvois_document_constraints(self, vals):
        constraints = {
            'myinvois_supplier_name_required': self._check_required_fields(vals['supplier'], 'name'),
            'myinvois_customer_name_required': self._check_required_fields(vals['customer'].commercial_partner_id, 'name'),
            'myinvois_document_name_required': self._check_required_fields(vals, 'document_name'),
        }

        if not vals['supplier'].commercial_partner_id.l10n_my_edi_industrial_classification:
            self._l10n_my_edi_make_validation_error(constraints, 'industrial_classification_required', 'supplier', vals['supplier'].display_name)

        for partner_type in ('supplier', 'customer'):
            partner = vals[partner_type]
            phone_number = partner.phone
            # 'NA' is a valid value in some cases, e.g. consolidated invoices.
            if phone_number != 'NA':
                phone = self._l10n_my_edi_get_formatted_phone_number(phone_number)
                if E_164_REGEX.match(phone) is None:
                    self._l10n_my_edi_make_validation_error(constraints, 'phone_number_format', partner_type, partner.display_name)
            elif not phone_number:
                self._l10n_my_edi_make_validation_error(constraints, 'phone_number_required', partner_type, partner.display_name)

            # We need to provide both l10n_my_identification_type and l10n_my_identification_number
            if not partner.commercial_partner_id.l10n_my_identification_type or not partner.commercial_partner_id.l10n_my_identification_number:
                self._l10n_my_edi_make_validation_error(constraints, 'required_id', partner_type, partner.commercial_partner_id.display_name)

            if not partner.state_id:
                self._l10n_my_edi_make_validation_error(constraints, 'no_state', partner_type, partner.display_name)
            if not partner.city:
                self._l10n_my_edi_make_validation_error(constraints, 'no_city', partner_type, partner.display_name)
            if not partner.country_id:
                self._l10n_my_edi_make_validation_error(constraints, 'no_country', partner_type, partner.display_name)
            if not partner.street:
                self._l10n_my_edi_make_validation_error(constraints, 'no_street', partner_type, partner.display_name)

            if partner.commercial_partner_id.sst_registration_number and len(partner.commercial_partner_id.sst_registration_number.split(';')) > 2:
                self._l10n_my_edi_make_validation_error(constraints, 'too_many_sst', partner_type, partner.commercial_partner_id.display_name)

        for line_vals in vals['document_node']['cac:InvoiceLine']:
            line_item = line_vals['cac:Item']
            if 'cac:CommodityClassification' not in line_item:
                self._l10n_my_edi_make_validation_error(constraints, 'class_code_required', line_vals['cbc:ID']['_text'], line_item['cbc:Name']['_text'])
            if not line_item.get('cac:ClassifiedTaxCategory'):
                self._l10n_my_edi_make_validation_error(constraints, 'tax_ids_required', line_vals['cbc:ID']['_text'], line_item['cbc:Name']['_text'])
            for tax_category in line_item['cac:ClassifiedTaxCategory']:
                if tax_category['cbc:ID']['_text'] == 'E' and not tax_category['cbc:TaxExemptionReason']['_text']:
                    self._l10n_my_edi_make_validation_error(constraints, 'tax_exemption_required', line_vals['cbc:ID']['_text'], line_item['cbc:Name']['_text'])

            myinvois_document = vals["myinvois_document"]
            if myinvois_document._is_consolidated_invoice() or myinvois_document._is_consolidated_invoice_refund():
                customer_vat = vals['document_node']['cac:AccountingCustomerParty']['cac:Party']['cac:PartyIdentification'][0]['cbc:ID']['_text']
                if customer_vat != 'EI00000000010':
                    self._l10n_my_edi_make_validation_error(constraints, 'missing_general_public', vals['customer'].id, vals['customer'].name)

        return constraints