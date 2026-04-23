def _add_myinvois_document_config_vals(self, vals):
        myinvois_document = vals['myinvois_document']
        supplier = myinvois_document.company_id.partner_id.commercial_partner_id

        if myinvois_document._is_consolidated_invoice() or myinvois_document._is_consolidated_invoice_refund():
            customer = self.env["res.partner"].search(
                domain=[
                    *self.env['res.partner']._check_company_domain(myinvois_document.company_id),
                    '|',
                    ('vat', '=', 'EI00000000010'),
                    ('l10n_my_edi_malaysian_tin', '=', 'EI00000000010'),
                ],
                limit=1,
            )
            partner_shipping = None
            payment_term_id = None  # wouldn't make sense in a consolidated invoice.
        else:
            invoice = myinvois_document.invoice_ids[0]  # Otherwise it would be a consolidated invoice.
            customer = invoice.partner_id
            partner_shipping = invoice.partner_shipping_id or customer
            payment_term_id = invoice.invoice_payment_term_id

        document_type_code, original_document = self._l10n_my_edi_get_document_type_code(myinvois_document)
        # In case of self billing, we want to invert the supplier and customer.
        if document_type_code in ("11", "12", "13", "14"):
            supplier, customer = customer, supplier
            partner_shipping = customer
            # In practice, we should never have multiple self billed invoices being part of a consolidated invoices,
            # but it doesn't hurt to support it.
            document_ref = ','.join([invoice.ref for invoice in myinvois_document.invoice_ids if invoice.ref]) or None
        else:
            document_ref = None

        vals.update({
            'document_type': 'invoice',
            'document_type_code': document_type_code,
            'original_document': original_document,

            'document_name': myinvois_document.name,

            'supplier': supplier,
            'customer': customer,
            'partner_shipping': partner_shipping,

            'company': myinvois_document.company_id,
            'currency_id': myinvois_document.currency_id,
            'company_currency_id': myinvois_document.company_id.currency_id,

            'use_company_currency': False,
            'fixed_taxes_as_allowance_charges': True,
            'custom_form_reference': myinvois_document.myinvois_custom_form_reference,
            'document_ref': document_ref,
            'incoterm_id': myinvois_document.invoice_ids.invoice_incoterm_id,
            'invoice_payment_term_id': payment_term_id,
        })