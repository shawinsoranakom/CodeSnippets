def _l10n_tw_edi_generate_ecpay_json(self, invoice, invoice_data):
        need_file = (
            ((invoice_data['invoice_edi_format'] == 'tw_ecpay'
                or 'manual' in invoice_data['sending_methods'])
                and invoice.company_id._is_ecpay_enabled())
            or 'tw_ecpay_send' in invoice_data['extra_edis']
            or 'tw_ecpay_issue_allowance' in invoice_data['extra_edis']
        )
        file_name = ''
        json_content = {}
        # It should always be generated when sending and downloading.
        if need_file:
            if 'tw_ecpay_send' in invoice_data['extra_edis']:
                json_content = invoice._l10n_tw_edi_generate_invoice_json()
                file_name = f'{invoice.name.replace("/", "_")}_ecpay.json'
            elif 'tw_ecpay_issue_allowance' in invoice_data['extra_edis']:
                json_content = invoice._l10n_tw_edi_generate_issue_allowance_json()
                file_name = f'{invoice.name.replace("/", "_")}_ecpay_issue_allowance.json'
            invoice_data['ecpay_attachments'] = {
                'name': file_name,
                'raw': json.dumps(json_content),
                'mimetype': 'application/json',
                'res_model': invoice._name,
                'res_id': invoice.id,
                'res_field': 'l10n_tw_edi_file',  # Binary field
            }