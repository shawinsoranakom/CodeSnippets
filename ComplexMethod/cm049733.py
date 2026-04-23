def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_before_invoice_pdf_render(invoices_data)

        for invoice, invoice_data in invoices_data.items():
            if any(key in invoice_data['extra_edis'] for key in ('tw_ecpay_send', 'tw_ecpay_issue_allowance')):
                if 'ecpay_attachments' in invoice_data:
                    json_content = json.loads(invoice_data['ecpay_attachments']['raw'])
                # If the invoice was downloaded but not sent, the json file could already be there.
                elif invoice.l10n_tw_edi_file:
                    json_content = json.loads(base64.b64decode(invoice.l10n_tw_edi_file))
                # If we don't have the file data and the file, we will regenerate it.
                else:
                    self._l10n_tw_edi_generate_ecpay_json(invoice, invoice_data)
                    if 'ecpay_attachments' not in invoice_data:
                        continue  # If an error occurred, it'll be in invoice_data['error'] so we can skip this invoice
                    json_content = json.loads(invoice_data['ecpay_attachments']['raw'])

            if 'tw_ecpay_send' in invoice_data['extra_edis']:
                if errors := invoice._l10n_tw_edi_send(json_content):
                    invoice_data["error"] = {
                        "error_title": self.env._("Error when sending the invoices to ECPay."),
                        "errors": errors,
                    }
            elif 'tw_ecpay_issue_allowance' in invoice_data['extra_edis']:
                if errors := invoice._l10n_tw_edi_issue_allowance(json_content):
                    invoice_data["error"] = {
                        "error_title": self.env._("Error when sending the allowances to ECPay."),
                        "errors": errors,
                    }
            if 'tw_ecpay_send' in invoice_data['extra_edis'] or 'tw_ecpay_issue_allowance' in invoice_data['extra_edis']:
                if self._can_commit():
                    self._cr.commit()