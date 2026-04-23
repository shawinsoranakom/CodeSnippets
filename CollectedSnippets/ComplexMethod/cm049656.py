def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_after_invoice_pdf_render(invoices_data)

        for invoice, invoice_data in invoices_data.items():
            # MojEracun determines the receiver endpoint entirely from the XML,
            # so there is no need to check for partner endpoint
            if 'mojeracun' not in invoice_data['sending_methods']:
                continue
            if not self._is_applicable_to_move('mojeracun', invoice, **invoice_data):
                raise UserError(self.env._("Failed to send invoice via MojEracun: check configuration."))

            if invoice_data.get('ubl_cii_xml_attachment_values'):
                xml_file = invoice_data['ubl_cii_xml_attachment_values']['raw']
            elif invoice.ubl_cii_xml_id and invoice.l10n_hr_mer_document_status not in {'20', '30', '40'}:
                xml_file = invoice.ubl_cii_xml_id.raw
            else:
                invoice.l10n_hr_edi_addendum_id.mer_document_status = '50'
                builder = invoice.partner_id.commercial_partner_id._get_edi_builder(invoice_data['invoice_edi_format'])
                invoice_data['error'] = self.env._(
                    "Errors occurred while creating the EDI document (format: %s):",
                    builder._description,
                )
                return
            addendum = invoice.l10n_hr_edi_addendum_id
            try:
                response = _mer_api_send(invoice.company_id, xml_file.decode())
            except MojEracunServiceError as e:
                addendum.mer_document_status = '50'
                invoice_data['error'] = e.message
            else:
                if not response.get('ElectronicId'):
                    addendum.mer_document_status = '50'
                    errors = []
                    for key in response:
                        errors.append(' '.join(response[key].get('Messages', [])))
                    invoice_data['error'] = {'error_title': "Error", 'errors': errors}
                else:
                    addendum.mer_document_eid = response['ElectronicId']
                    addendum.mer_document_status = '20'
                    log_message = self.env._('The document has been sent to MojEracun service provider for processing')
                    invoice._message_log(body=log_message)
            if self._can_commit():
                self.env.cr.commit()