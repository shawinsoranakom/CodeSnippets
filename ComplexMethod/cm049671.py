def _l10n_sa_run_compliance_checks(self):
        """
            Run Compliance Checks once the CCSID has been obtained.

            The goal of the Compliance Checks is to make sure our system is able to produce, sign and send Invoices
            correctly. For this we use dummy invoice UBL files available under the tests/compliance folder:

            Standard Invoice, Standard Credit Note, Standard Debit Note, Simplified Invoice, Simplified Credit Note,
            Simplified Debit Note.

            We read each one of these files separately, sign them, then process them through the Compliance Checks API.
        """

        self.ensure_one()
        self_sudo = self.sudo()
        if self.country_code != 'SA':
            raise UserError(_("Please change the (%s)'s country to Saudi Arabia and try again.", self.company_id.name))
        if not self_sudo.l10n_sa_compliance_csid_json or not self_sudo.l10n_sa_compliance_csid_certificate_id:
            raise UserError(str(ERROR_MESSAGE))
        CCSID_data = json.loads(self_sudo.l10n_sa_compliance_csid_json)
        compliance_files = self._l10n_sa_get_compliance_files()
        for fname, fval in compliance_files.items():
            invoice_hash_hex = self.env['account.edi.xml.ubl_21.zatca']._l10n_sa_generate_invoice_xml_hash(
                fval).decode()
            digital_signature = self.env.ref('l10n_sa_edi.edi_sa_zatca')._l10n_sa_get_digital_signature(self.company_id, invoice_hash_hex).decode()
            prepared_xml = self._l10n_sa_prepare_compliance_xml(fname, fval, self_sudo.l10n_sa_compliance_csid_certificate_id, digital_signature)
            result = self._l10n_sa_api_compliance_checks(prepared_xml.decode(), CCSID_data)
            if result.get('error'):
                raise UserError(Markup("<p class='mb-0'>%s</p>") % (str(ERROR_MESSAGE)))
            if result['validationResults']['status'] == 'WARNING':
                warnings = Markup().join(Markup("<li><b>%(code)s</b>: %(message)s </li>") % e for e in result['validationResults']['warningMessages'])
                self.l10n_sa_csr_errors = Markup("<br/><br/><ul class='pl-3'><b>%s</b>%s</ul>") % (_("Warnings:"), warnings)
            elif result['validationResults']['status'] != 'PASS':
                raise UserError(Markup("<p class='mb-0'>%s</p>") % (str(ERROR_MESSAGE)))
        self.l10n_sa_compliance_checks_passed = True