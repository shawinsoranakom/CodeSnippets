def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_before_invoice_pdf_render(invoices_data)
        for invoice, invoice_data in invoices_data.items():
            if 'vn_sinvoice_send' in invoice_data['extra_edis']:
                errors = invoice._l10n_vn_edi_check_invoice_configuration()
                if not errors:
                    if 'sinvoice_attachments' in invoice_data:
                        json_data = json.loads(invoice_data['sinvoice_attachments'][0]['raw'].decode('utf-8'))
                    # If the invoice was downloaded but not sent, the json file could already be there.
                    elif invoice.l10n_vn_edi_sinvoice_file:
                        json_data = json.loads(base64.b64decode(invoice.l10n_vn_edi_sinvoice_file).decode('utf-8'))
                    # If we don't have the file data and the file, we will regenerate it.
                    else:
                        self._generate_sinvoice_file_date(invoice, invoice_data)
                        # In case the above call ended in an error, we skip setting json_data
                        if 'sinvoice_attachments' not in invoice_data:
                            continue
                        json_data = json.loads(invoice_data['sinvoice_attachments'][0]['raw'].decode('utf-8'))
                    if json_data:
                        errors = invoice._l10n_vn_edi_send_invoice(json_data)

                if errors:
                    invoice_data['error'] = {
                        'error_title': _('Error when sending to SInvoice'),
                        'errors': errors,
                    }

                if self._can_commit():
                    self.env.cr.commit()