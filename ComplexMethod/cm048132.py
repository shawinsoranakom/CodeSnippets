def _l10n_es_edi_sii_send(self, invoices, cancel=False):
        # Ensure a certificate is available.
        certificate = invoices.company_id.l10n_es_sii_certificate_id
        if not certificate:
            return {inv: {
                'error': _("Please configure the certificate for SII."),
                'blocking_level': 'error',
            } for inv in invoices}

        # Ensure a tax agency is available.
        l10n_es_sii_tax_agency = invoices.company_id.mapped('l10n_es_sii_tax_agency')[0]
        if not l10n_es_sii_tax_agency:
            return {inv: {
                'error': _("Please specify a tax agency on your company for SII."),
                'blocking_level': 'error',
            } for inv in invoices}

        # Generate the JSON.
        info_list = self._l10n_es_edi_get_invoices_info(invoices)

        # Call the web service.
        if not cancel: #retrocompatibility and mocks in tests
            res = self._l10n_es_edi_call_web_service_sign(invoices, info_list)
        else:
            res = self._l10n_es_edi_call_web_service_sign_common(invoices, info_list, cancel=True)

        for inv in invoices:
            if res.get(inv, {}).get('success'):
                attachment = self.env['ir.attachment'].create({
                    'type': 'binary',
                    'name': 'jsondump.json',
                    'raw': json.dumps(info_list),
                    'mimetype': 'application/json',
                    'res_model': inv._name,
                    'res_id': inv.id,
                })
                res[inv]['attachment'] = attachment
                if cancel:
                    inv.l10n_es_edi_csv = False
        return res