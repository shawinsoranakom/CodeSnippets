def _export_invoice_vals(self, invoice):
        customer = invoice.partner_id
        supplier = invoice.company_id.partner_id.commercial_partner_id

        def format_date(dt):
            # Format the date in the Factur-x standard.
            dt = dt or datetime.now()
            return dt.strftime(DEFAULT_FACTURX_DATE_FORMAT)

        def format_monetary(number, decimal_places=2):
            # Facturx requires the monetary values to be rounded to 2 decimal values
            return float_repr(number, decimal_places)

        def grouping_key_generator(base_line, tax_data):
            tax = tax_data['tax']
            grouping_key = {
                'tax_category_code': self._get_tax_category_code(customer.commercial_partner_id, supplier, tax),
                **self._get_tax_exemption_reason(customer.commercial_partner_id, supplier, tax),
                'amount': tax.amount,
                'amount_type': tax.amount_type,
            }
            # If the tax is fixed, we want to have one group per tax
            # s.t. when the invoice is imported, we can try to guess the fixed taxes
            if tax.amount_type == 'fixed':
                grouping_key['tax_name'] = tax.name
            return grouping_key

        # Validate the structure of the taxes
        self._validate_taxes(invoice.invoice_line_ids.tax_ids)

        # Create file content.
        tax_details = invoice._prepare_invoice_aggregated_taxes(grouping_key_generator=grouping_key_generator)

        # Fixed Taxes: filter them on the document level, and adapt the totals
        # Fixed taxes are not supposed to be taxes in real live. However, this is the way in Odoo to manage recupel
        # taxes in Belgium. Since only one tax is allowed, the fixed tax is removed from totals of lines but added
        # as an extra charge/allowance.
        fixed_taxes_keys = [k for k in tax_details['tax_details'] if k['amount_type'] == 'fixed']
        for key in fixed_taxes_keys:
            fixed_tax_details = tax_details['tax_details'].pop(key)
            tax_details['tax_amount_currency'] -= fixed_tax_details['tax_amount_currency']
            tax_details['tax_amount'] -= fixed_tax_details['tax_amount']
            tax_details['base_amount_currency'] += fixed_tax_details['tax_amount_currency']
            tax_details['base_amount'] += fixed_tax_details['tax_amount']

        template_values = {
            **invoice._prepare_edi_vals_to_export(),
            'tax_details': tax_details,
            'format_date': format_date,
            'format_monetary': format_monetary,
            'is_html_empty': is_html_empty,
            'scheduled_delivery_time': self._get_scheduled_delivery_time(invoice),
            'intracom_delivery': False,
            'ExchangedDocument_vals': self._get_exchanged_document_vals(invoice),
            'seller_specified_legal_organization': invoice.company_id.company_registry,
            'buyer_specified_legal_organization': invoice.commercial_partner_id.company_registry,
            'ship_to_trade_party': invoice.partner_shipping_id if 'partner_shipping_id' in invoice._fields and invoice.partner_shipping_id
                else invoice.commercial_partner_id,
            # Chorus Pro fields
            'buyer_reference': invoice.buyer_reference if 'buyer_reference' in invoice._fields
                and invoice.buyer_reference else invoice.commercial_partner_id.ref,
            'purchase_order_reference': invoice.purchase_order_reference if 'purchase_order_reference' in invoice._fields
                and invoice.purchase_order_reference else invoice.ref or invoice.name,
            'contract_reference': invoice.contract_reference if 'contract_reference' in invoice._fields and invoice.contract_reference else '',
            'document_context_id': "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:extended",
        }

        # data used for IncludedSupplyChainTradeLineItem / SpecifiedLineTradeSettlement
        for line_vals in template_values['invoice_line_vals_list']:
            line = line_vals['line']
            line_vals['unece_uom_code'] = self._get_uom_unece_code(line.product_uom_id)

            if line._fields.get('deferred_start_date') and (line.deferred_start_date or line.deferred_end_date):
                line_vals['billing_start'] = line.deferred_start_date
                line_vals['billing_end'] = line.deferred_end_date

        # [BR - IC - 11] - In an Invoice with a VAT breakdown (BG-23) where the VAT category code (BT-118) is
        # "Intra-community supply" the Actual delivery date (BT-72) or the Invoicing period (BG-14) shall not be blank.
        billing_start_dates = [invoice.invoice_date] if invoice.invoice_date else []
        billing_start_dates += [line_vals['billing_start'] for line_vals in template_values['invoice_line_vals_list'] if line_vals.get('billing_start')]
        billing_end_dates = [invoice.invoice_date_due] if invoice.invoice_date_due else []
        billing_end_dates += [line_vals['billing_end'] for line_vals in template_values['invoice_line_vals_list'] if line_vals.get('billing_end')]
        if billing_start_dates:
            template_values['billing_start'] = min(billing_start_dates)
        if billing_end_dates:
            template_values['billing_end'] = max(billing_end_dates)

        # data used for ApplicableHeaderTradeSettlement / ApplicableTradeTax (at the end of the xml)
        for tax_detail_vals in template_values['tax_details']['tax_details'].values():
            # /!\ -0.0 == 0.0 in python but not in XSLT, so it can raise a fatal error when validating the XML
            # if 0.0 is expected and -0.0 is given.
            amount_currency = tax_detail_vals['tax_amount_currency']
            tax_detail_vals['calculated_amount'] = amount_currency if not invoice.currency_id.is_zero(amount_currency) else 0

            if tax_detail_vals.get('tax_category_code') == 'K':
                template_values['intracom_delivery'] = True

        # Fixed taxes: add them as charges on the invoice lines
        for line_vals in template_values['invoice_line_vals_list']:
            line_vals['allowance_charge_vals_list'] = []
            for grouping_key, tax_detail in tax_details['tax_details_per_record'][line_vals['line']]['tax_details'].items():
                if grouping_key['amount_type'] == 'fixed':
                    line_vals['allowance_charge_vals_list'].append({
                        'indicator': 'true',
                        'reason': tax_detail['tax_name'],
                        'reason_code': 'AEO',
                        'amount': tax_detail['tax_amount_currency'],
                    })
            sum_fixed_taxes = sum(x['amount'] for x in line_vals['allowance_charge_vals_list'])
            line_vals['line_total_amount'] = line_vals['line'].price_subtotal + sum_fixed_taxes

            # The quantity is the line.quantity since we keep the unece_uom_code!
            line_vals['quantity'] = line_vals['line'].quantity

            # Invert the quantity and the gross_price_total_unit if a line has a negative price total
            if line_vals['line'].currency_id.compare_amounts(line_vals['gross_price_total_unit'], 0) == -1:
                line_vals['quantity'] *= -1
                line_vals['gross_price_total_unit'] *= -1
                line_vals['price_subtotal_unit'] *= -1

        # Fixed taxes: set the total adjusted amounts on the document level
        template_values['tax_basis_total_amount'] = tax_details['base_amount_currency']
        template_values['tax_total_amount'] = tax_details['tax_amount_currency']

        if self.env['account.payment']._fields.get('sdd_mandate_id') and invoice.reconciled_payment_ids.sdd_mandate_id:
            template_values['payment_means_code'] = PAYMENT_MEAN_CODES['SEPA direct debit']
        else:
            template_values['payment_means_code'] = PAYMENT_MEAN_CODES['Payment to bank account']

        return template_values