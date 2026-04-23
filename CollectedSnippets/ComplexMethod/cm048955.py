def _add_myinvois_document_header_nodes(self, document_node, vals):
        original_document_id = None
        if vals['document_type_code'] in {'02', '03', '04', '12', '13', '14'} and vals['original_document']:
            if vals['original_document'].myinvois_file_id:
                decoded_vals = self._l10n_my_edi_decode_myinvois_attachment(vals['original_document'].myinvois_file_id)
                original_document_id = decoded_vals.get('original_document_id')
            original_invoice = vals['original_document'].invoice_ids[:1]
            if not original_document_id and vals['document_type_code'] in {'12', '13', '14'} and original_invoice.ref:
                original_document_id = original_invoice.ref
            if not original_document_id:
                original_document_id = vals['original_document'].name

        document_node.update({
            'cbc:UBLVersionID': None,
            'cbc:ID': {'_text': vals['document_name']},
            # The issue date and time must be the current time set in the UTC time zone
            'cbc:IssueDate': {'_text': datetime.now(tz=UTC).strftime("%Y-%m-%d")},
            'cbc:IssueTime': {'_text': datetime.now(tz=UTC).strftime("%H:%M:%SZ")},
            'cbc:DueDate': None,

            # The current version is 1.1 (document with signature), the type code depends on the move type.
            'cbc:InvoiceTypeCode': {
                '_text': vals['document_type_code'],
                'listVersionID': '1.1',
            },
            'cbc:DocumentCurrencyCode': {'_text': vals['currency_id'].name},
            'cac:OrderReference': None,
            'cbc:BuyerReference': {'_text': vals['customer'].commercial_partner_id.ref},

            # Debit/Credit note original invoice ref.
            # Applies to credit notes, debit notes, refunds for both invoices and self-billed invoices.
            # The original document is mandatory; but in some specific cases it will be empty (sending a credit note for an invoice
            # managed outside Odoo/...)
            'cac:BillingReference': {
                'cac:InvoiceDocumentReference': {
                    'cbc:ID': {'_text': original_document_id or 'NA'},
                    'cbc:UUID': {'_text': (vals['original_document'] and vals['original_document'].myinvois_external_uuid) or 'NA'},
                }
            } if vals['document_type_code'] in {'02', '03', '04', '12', '13', '14'} else None,
            'cac:AdditionalDocumentReference': [
                {
                    'cbc:ID': {'_text': vals['custom_form_reference']},
                    'cbc:DocumentType': {'_text': 'CustomsImportForm'},
                } if vals['document_type_code'] in {'11', '12', '13', '14'} and vals['custom_form_reference'] else None,
                {
                    'cbc:ID': {'_text': vals["incoterm_id"].code}
                } if vals["incoterm_id"] else None,
                {
                    'cbc:ID': {'_text': vals['custom_form_reference']},
                    'cbc:DocumentType': {'_text': 'K2'},
                } if vals['document_type_code'] in {'01', '02', '03', '04'} and vals['custom_form_reference'] else None,
            ],
        })

        # Self-billed invoices must use the number given by the supplier.
        if vals['document_type_code'] in ('11', '12', '13', '14') and vals['document_ref']:
            document_node['cbc:ID']['_text'] = vals['document_ref']