def _l10n_es_edi_facturae_export_facturae(self):
        """
        Produce the Facturae XML data for the invoice.

        :return: (data needed to render the full template, data needed to render the signature template)
        """
        def extract_party_name(party):
            name = {'firstname': 'UNKNOWN', 'surname': 'UNKNOWN', 'surname2': ''}
            if not party.is_company:
                name_split = [part for part in party.name.replace(', ', ' ').split(' ') if part]
                if len(name_split) > 2:
                    name['firstname'] = ' '.join(name_split[:-2])
                    name['surname'], name['surname2'] = name_split[-2:]
                elif len(name_split) == 2:
                    name['firstname'] = ' '.join(name_split[:-1])
                    name['surname'] = name_split[-1]
            return name

        self.ensure_one()
        company = self.company_id
        partner = self.commercial_partner_id

        if not company.vat:
            raise UserError(_('The company needs a set tax identification number or VAT number'))
        if not partner.vat:
            raise UserError(_('The partner needs a set tax identification number or VAT number'))
        if not partner.country_id:
            raise UserError(_("The partner needs a set country"))
        if self.move_type == "entry":
            return False

        operation_date = None
        if self.delivery_date and self.delivery_date != self.invoice_date:
            operation_date = self.delivery_date.isoformat()

        # Multi-currencies.
        eur_curr = self.env['res.currency'].search([('name', '=', 'EUR')])
        inv_curr = self.currency_id
        conversion_needed = inv_curr != eur_curr

        # Invoice xml values.
        invoice_ref = self.ref and self.ref[:20]
        legal_literals = self.narration and self.narration.striptags()
        legal_literals = legal_literals.split(";") if legal_literals else False
        invoice_values = {
            'invoice_record': self,
            'invoice_currency': inv_curr,
            'InvoiceDocumentType': 'FA' if self.l10n_es_is_simplified else 'FC',
            'InvoiceClass': 'OR' if self.move_type in ['out_refund', 'in_refund'] else 'OO',
            'Corrective': self._l10n_es_edi_facturae_get_corrective_data(),
            'InvoiceIssueData': {
                'OperationDate': operation_date,
                'ExchangeRateDetails': conversion_needed,
                'ExchangeRate': f"{round(self.invoice_currency_rate, 4):.4f}",
                'LanguageName': self.env.context.get('lang', 'en_US').split('_')[0],
                'InvoicingPeriod': None,
                'ReceiverTransactionReference': invoice_ref,
                'FileReference': invoice_ref,
                'ReceiverContractReference': invoice_ref,
            },
            'TaxOutputs': [],
            'TaxesWithheld': [],
            'TotalGrossAmount': 0.0,
            'TotalGeneralDiscounts': 0.0,
            'TotalGeneralSurcharges': 0.0,
            'TotalGrossAmountBeforeTaxes': 0.0,
            'TotalTaxOutputs': 0.0,
            'TotalTaxesWithheld': 0.0,
            'PaymentsOnAccount': [],
            'TotalOutstandingAmount': abs(self.amount_total_in_currency_signed),
            'InvoiceTotal': abs(self.amount_total_in_currency_signed),
            'TotalPaymentsOnAccount': 0.0,
            'AmountsWithheld': None,
            'TotalExecutableAmount': abs(self.amount_total_in_currency_signed),
            'Items': [],
            'PaymentDetails': self._l10n_es_edi_facturae_convert_payment_terms_to_installments(),
            'LegalLiterals': legal_literals,
        }

        # Taxes.
        AccountTax = self.env['account.tax']
        base_lines, _tax_lines = self._get_rounded_base_and_tax_lines()

        def grouping_function_per_tax(base_line, tax_data):
            return tax_data['tax'] if tax_data else None

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_per_tax)
        for base_line, aggregated_values in base_lines_aggregated_values:
            invoice_line_values = self._l10n_es_edi_facturae_prepare_inv_line(base_line, aggregated_values)
            invoice_values['TotalGrossAmount'] += invoice_line_values['GrossAmount']
            invoice_values['Items'].append(invoice_line_values)

        def grouping_function_per_base_line_tax(base_line, tax_data):
            if not tax_data:
                return
            return {
                'tax_es_type': tax_data['tax'].l10n_es_edi_facturae_tax_type,
                'tax_rate': tax_data['tax'].amount,
                'tax_amount_type': tax_data['tax'].amount_type,
            }

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_per_base_line_tax)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            if not grouping_key:
                continue
            tax_record = values['base_line_x_taxes_data'][0][1][0]['tax']
            if not tax_record:
                continue

            is_withholding = values['grouping_key']['tax_rate'] < 0.0
            tax_data = self._l10n_es_edi_facturae_get_tax_node_from_tax_data({**values, 'grouping_key': tax_record}, round=True)
            if is_withholding:
                invoice_values['TaxesWithheld'].append(tax_data)
                invoice_values['TotalTaxesWithheld'] -= values['tax_amount_currency']
            else:
                invoice_values['TaxOutputs'].append(tax_data)
                invoice_values['TotalTaxOutputs'] += values['tax_amount_currency']

        invoice_values['TotalTaxesWithheld'] = abs(invoice_values['TotalTaxesWithheld'])

        invoice_values['TotalGrossAmountBeforeTaxes'] = (
            invoice_values['TotalGrossAmount']
            - invoice_values['TotalGeneralDiscounts']
            + invoice_values['TotalGeneralSurcharges']
        )
        refund_multiplier = -1 if self.move_type in ('out_refund', 'in_refund') else 1

        template_values = {
            'self_party': company.partner_id,
            'self_party_country_code': COUNTRY_CODE_MAP[company.country_id.code],
            'self_party_name': extract_party_name(company.partner_id),
            'self_party_administrative_centers': self._l10n_es_edi_facturae_get_administrative_centers(company.partner_id),
            'other_party': partner,
            'other_party_country_code': COUNTRY_CODE_MAP[partner.country_id.code],
            'other_party_phone': partner.phone.translate(PHONE_CLEAN_TABLE) if partner.phone else False,
            'other_party_name': extract_party_name(partner),
            'other_party_administrative_centers': self._l10n_es_edi_facturae_get_administrative_centers(partner),
            'is_outstanding': self.move_type.startswith('out_'),
            'float_repr': float_repr,
            'file_currency': inv_curr,
            'eur': eur_curr,
            'conversion_needed': conversion_needed,
            'refund_multiplier': refund_multiplier,

            'Modality': 'I',
            'BatchIdentifier': self.name,
            'InvoicesCount': 1,
            'TotalInvoicesAmount': {
                'TotalAmount': abs(self.amount_total_in_currency_signed),
                'EquivalentInEuros': abs(self.amount_total_signed),
            },
            'TotalOutstandingAmount': {
                'TotalAmount': abs(self.amount_total_in_currency_signed),
                'EquivalentInEuros': abs(self.amount_total_signed),
            },
            'TotalExecutableAmount': {
                'TotalAmount': abs(self.amount_total_in_currency_signed),
                'EquivalentInEuros': abs(self.amount_total_signed),
            },
            'InvoiceCurrencyCode': inv_curr.name,
            'Invoices': [invoice_values],
        }

        if self.l10n_es_invoicing_period_start_date and self.l10n_es_invoicing_period_end_date:
            template_values['Invoices'][0]['InvoiceIssueData']['InvoicingPeriod'] = {
                'StartDate': self.l10n_es_invoicing_period_start_date,
                'EndDate': self.l10n_es_invoicing_period_end_date,
            }

        invoice_issuer_signature_type = 'supplier' if self.move_type == 'out_invoice' else 'customer'
        signature_values = {'SigningTime': '', 'SignerRole': invoice_issuer_signature_type}
        return template_values, signature_values