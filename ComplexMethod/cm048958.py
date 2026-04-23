def _l10n_my_edi_get_document_type_code(self, myinvois_document):
        """ Returns the code matching the invoice type, as well as the original document if any. """
        document_type_code = '01'
        original_document = None

        if not myinvois_document._is_consolidated_invoice():
            invoice = myinvois_document.invoice_ids[0]  # Otherwise it would be a consolidated invoice.
            if 'debit_origin_id' in self.env['account.move']._fields and invoice.debit_origin_id:
                document_type_code = '03' if invoice.move_type == 'out_invoice' else '13'
                original_document = invoice.debit_origin_id._get_active_myinvois_document()
            elif invoice.move_type in ('out_refund', 'in_refund'):
                is_refund, refunded_document = self._l10n_my_edi_get_refund_details(invoice)
                if is_refund:
                    document_type_code = '04' if invoice.move_type == 'out_refund' else '14'
                else:
                    document_type_code = '02' if invoice.move_type == 'out_refund' else '12'

                original_document = refunded_document
            else:
                document_type_code = '01' if invoice.move_type == 'out_invoice' else '11'

        return document_type_code, original_document