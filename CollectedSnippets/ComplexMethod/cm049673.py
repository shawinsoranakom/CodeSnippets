def _l10n_sa_submit_einvoice(self, invoice, signed_xml, PCSID_data):
        """
            Submit a generated Invoice UBL file by making calls to the following APIs:
                -   A. Clearance API: Submit a standard Invoice to ZATCA for validation, returns signed UBL
                -   B. Reporting API: Submit a simplified Invoice to ZATCA for validation
        """
        clearance_data = invoice.journal_id._l10n_sa_api_clearance(invoice, signed_xml.decode(), PCSID_data)
        if error := clearance_data.get('json_errors'):
            error_msg = ''
            if status_code := error.get('status_code'):
                error_msg = Markup("<b>[%s] </b>") % status_code

            is_warning = True
            validation_results = error.get('validationResults', {})
            for err in validation_results.get('warningMessages', []):
                error_msg += Markup('<b>%s</b> : %s <br/>') % (err['code'], err['message'])
            for err in validation_results.get('errorMessages', []):
                is_warning = False
                error_msg += Markup('<b>%s</b> : %s <br/>') % (err['code'], err['message'])
            return {
                'error': error_msg,
                'rejected': not is_warning,
                'response': signed_xml.decode(),
                'blocking_level': 'warning' if is_warning else 'error',
                'status_code': status_code,
            }
        if not clearance_data.get('error') and clearance_data.get("status_code") != 409:
            return self._l10n_sa_assert_clearance_status(invoice, clearance_data)
        return clearance_data