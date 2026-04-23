def _add_invoice_header_nodes(self, document_node, vals):
        super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals['invoice']
        issue_date = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), invoice.l10n_sa_confirmation_datetime)

        document_node.update({
            'cbc:ProfileID': {'_text': 'reporting:1.0'},
            'cbc:UUID': {'_text': invoice.l10n_sa_uuid},
            'cbc:IssueDate': {'_text': issue_date.strftime('%Y-%m-%d')},
            'cbc:IssueTime': {'_text': issue_date.strftime('%H:%M:%S')},
            'cbc:DueDate': None,
            'cbc:InvoiceTypeCode': {
                '_text': (
                    383 if invoice.debit_origin_id else
                    381 if invoice.move_type == 'out_refund' else
                    386 if invoice._is_downpayment() else 388
                ),
                'name': '0%s00%s00' % (
                    '2' if invoice._l10n_sa_is_simplified() else '1',
                    '1' if invoice.commercial_partner_id.country_id != invoice.company_id.country_id and not invoice._l10n_sa_is_simplified() else '0'
                ),
            },
            'cbc:TaxCurrencyCode': {'_text': vals['company_currency_id'].name},
            'cac:OrderReference': None,
            'cac:BillingReference': {
                'cac:InvoiceDocumentReference': {
                    'cbc:ID': {
                        '_text': (invoice.reversed_entry_id.name or invoice.ref)
                        if invoice.move_type == 'out_refund'
                        else invoice.debit_origin_id.name
                    }
                }
            } if invoice.move_type == 'out_refund' or invoice.debit_origin_id else None,
            'cac:AdditionalDocumentReference': [
                {
                    'cbc:ID': {'_text': 'QR'},
                    'cac:Attachment': {
                        'cbc:EmbeddedDocumentBinaryObject': {
                            '_text': 'N/A',
                            'mimeCode': 'text/plain',
                        }
                    }
                } if invoice._l10n_sa_is_simplified() else None,
                {
                    'cbc:ID': {'_text': 'PIH'},
                    'cac:Attachment': {
                        'cbc:EmbeddedDocumentBinaryObject': {
                            '_text': (
                                "NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=="
                                if invoice.company_id.l10n_sa_api_mode == 'sandbox' or not invoice.journal_id.l10n_sa_latest_submission_hash
                                else invoice.journal_id.l10n_sa_latest_submission_hash
                            ),
                            'mimeCode': 'text/plain',
                        }
                    }
                },
                {
                    'cbc:ID': {'_text': 'ICV'},
                    'cbc:UUID': {'_text': invoice.l10n_sa_chain_index},
                }
            ],
            'cac:Signature': {
                'cbc:ID': {'_text': "urn:oasis:names:specification:ubl:signature:Invoice"},
                'cbc:SignatureMethod': {'_text': "urn:oasis:names:specification:ubl:dsig:enveloped:xades"},
            } if invoice._l10n_sa_is_simplified() else None,
            'cac:PaymentTerms': None,
        })