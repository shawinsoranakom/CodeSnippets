def _l10n_sa_post_zatca_edi(self, invoice):  # no batch ensure that there is only one invoice
        """
            Post invoice to ZATCA and return a dict of invoices and their success/attachment
        """

        # Chain integrity check: chain head must have been REALLY posted, and did not time out
        # When a submission times out, we reset the chain index of the invoice to False, so it has to be submitted again
        # According to ZATCA, if we end up submitting the same invoice more than once, they will directly reach out
        # to the taxpayer for clarifications
        chain_head = invoice.journal_id._l10n_sa_get_last_posted_invoice()
        if chain_head and chain_head != invoice and not chain_head._l10n_sa_is_in_chain():
            invoice.l10n_sa_edi_chain_head_id = chain_head
            return {invoice: {
                'error': _("Error: This invoice is blocked due to %s. Please check it.", chain_head.name),
                'blocking_level': 'error',
                'response': None,
            }}

        xml_content = None
        if not invoice.l10n_sa_chain_index:
            # If the Invoice doesn't have a chain index, it means it either has not been submitted before,
            # or it was submitted and rejected. Either way, we need to assign it a new Chain Index and regenerate
            # the data that depends on it before submitting (UUID, XML content, signature)
            invoice.l10n_sa_chain_index = invoice.journal_id._l10n_sa_edi_get_next_chain_index()
            xml_content = invoice._l10n_sa_generate_unsigned_data()

        # Generate Invoice name for attachment
        attachment_name = self.env['account.edi.xml.ubl_21.zatca']._export_invoice_filename(invoice)

        # Generate XML, sign it, then submit it to ZATCA
        response_data, submitted_xml = self._l10n_sa_export_zatca_invoice(invoice, xml_content)

        # Check for submission errors
        if response_data.get('error'):

            # If the request was rejected, we save the signed xml content as an attachment
            # If request timedout, just log note a warning message
            invoice._l10n_sa_log_results(submitted_xml, response_data, error=response_data.get('rejected'))

            # If the request returned an exception (Timeout, ValueError... etc.) it means we're not sure if the
            # invoice was successfully cleared/reported, and thus we keep the Index Chain.
            # Else, we recalculate the submission Index (ICV), UUID, XML content and Signature
            if not response_data.get('excepted'):
                invoice.l10n_sa_chain_index = False

            return {
                invoice: {
                    **response_data,
                    'response': submitted_xml
                }
            }

        # Once submission is done with no errors, check submission status
        cleared_xml = self._l10n_sa_postprocess_einvoice_submission(invoice, submitted_xml, response_data)

        # Set 'l10n_sa_edi_is_production' to True upon the first invoice submission in Production mode
        if not invoice.company_id.l10n_sa_edi_is_production:
            invoice.company_id.l10n_sa_edi_is_production = invoice.company_id.l10n_sa_api_mode == 'prod'

        # Save the submitted/returned invoice XML content once the submission has been completed successfully
        invoice._l10n_sa_log_results(cleared_xml.encode(), response_data)
        invoice.journal_id._l10n_sa_reset_chain_head_error()
        return {
            invoice: {
                'success': True,
                'response': cleared_xml,
                'message': '',
                'attachment': self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'raw': cleared_xml.encode(),
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'mimetype': 'application/xml'
                })
            }
        }