def _add_invoice_header_nodes(self, document_node, vals):
        super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals['invoice']

        # Check the customer status if it hasn't been done before as it's needed for profile_id
        if invoice.partner_id.l10n_tr_nilvera_customer_status == 'not_checked':
            invoice.partner_id._check_nilvera_customer()

        if invoice._l10n_tr_nilvera_einvoice_check_negative_lines():
            raise UserError(self.env._("Nilvera portal cannot process negative quantity nor negative price on invoice lines"))

        # Using _get_sequence_format_param to extract the invoice sequence components for various formats.
        # To send an invoice to Nilvera, the format needs to follow ABC2009123456789.
        _, parts = invoice._get_sequence_format_param(invoice.name)
        prefix, year, number = parts['prefix1'][:3], parts['year'], str(parts['seq']).zfill(9)
        invoice_id = f"{prefix.upper()}{year}{number}"

        document_node.update({
            'cbc:CustomizationID': {'_text': 'TR1.2'},
            'cbc:ProfileID': {
                '_text': 'TEMELFATURA' if invoice.partner_id.l10n_tr_nilvera_customer_status == 'einvoice' else 'EARSIVFATURA'
            },
            'cbc:ID': {'_text': invoice_id},
            'cbc:CopyIndicator': {'_text': 'false'},
            'cbc:UUID': {'_text': invoice.l10n_tr_nilvera_uuid},
            'cbc:DueDate': None,
            'cbc:InvoiceTypeCode': {'_text': 'SATIS'} if vals['document_type'] == 'invoice' else None,
            'cbc:CreditNoteTypeCode': {'_text': 'IADE'} if vals['document_type'] == 'credit_note' else None,
            'cbc:PricingCurrencyCode': {'_text': invoice.currency_id.name.upper()}
                if vals['currency_id'] != vals['company_currency_id'] else None,
            'cbc:LineCountNumeric': {'_text': len(invoice.line_ids)},
            'cbc:BuyerReference': None,  # Nilvera will reject any <BuyerReference> tag, so remove it
            'cbc:Note': {
                '_text': html2plaintext(invoice.narration, include_references=False) if invoice.narration else None,
            },
        })

        if invoice.invoice_line_ids._fields.get('deferred_start_date'):
            line_ids = invoice.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line.deferred_start_date)
            if line_ids:
                document_node['cac:InvoicePeriod'] = {
                    'cbc:StartDate': {'_text': line_ids[0].deferred_start_date},
                    'cbc:EndDate': {'_text': line_ids[0].deferred_end_date},
                }

        document_node['cac:OrderReference']['cbc:IssueDate'] = {'_text': invoice.invoice_date}

        if invoice.partner_id.l10n_tr_nilvera_customer_status == 'earchive':
            document_node['cac:AdditionalDocumentReference'] = {
                'cbc:ID': {'_text': 'ELEKTRONIK'},
                'cbc:IssueDate': {'_text': invoice.invoice_date},
                'cbc:DocumentTypeCode': {'_text': 'SEND_TYPE'},
            }
        document_node['cbc:Note'] = [
            document_node['cbc:Note'],
            {'_text': self._l10n_tr_get_amount_integer_partn_text_note(invoice.amount_residual_signed, self.env.ref('base.TRY')), 'note_attrs': {}}
        ]
        if vals['invoice'].currency_id.name != 'TRY':
            document_node['cbc:Note'].append({'_text': self._l10n_tr_get_amount_integer_partn_text_note(invoice.amount_residual, vals['invoice'].currency_id), 'note_attrs': {}})
            document_node['cbc:Note'].append({'_text': f'KUR : {self._l10n_tr_get_currency_conversion_rate(invoice):.6f} TL'})