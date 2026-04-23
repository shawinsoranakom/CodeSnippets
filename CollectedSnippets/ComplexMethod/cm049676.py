def _prepare_invoice_report(self, pdf_writer, edi_document):
        """
        Prepare invoice report to be printed.
        :param pdf_writer: The pdf writer with the invoice pdf content loaded.
        :param edi_document: The edi document to be added to the pdf file.
        """
        self.ensure_one()
        super()._prepare_invoice_report(pdf_writer, edi_document)
        if self.code != 'sa_zatca' or edi_document.move_id.country_code != 'SA':
            return

        attachment = edi_document.sudo().attachment_id
        if not attachment or not attachment.datas:
            _logger.warning("No attachment found for invoice %s", edi_document.move_id.name)
            return

        xml_content = attachment.raw
        file_name = attachment.name

        pdf_writer.addAttachment(file_name, xml_content, subtype='text/xml')
        if not pdf_writer.is_pdfa:
            try:
                pdf_writer.convert_to_pdfa()
            except Exception:
                _logger.exception("Error while converting to PDF/A")
            content = self.env['ir.qweb']._render(
                'account_edi_ubl_cii.account_invoice_pdfa_3_facturx_metadata',
                {
                    'title': edi_document.move_id.name,
                    'date': fields.Date.context_today(self),
                },
            )
            if "<pdfaid:conformance>B</pdfaid:conformance>" in content:
                content.replace("<pdfaid:conformance>B</pdfaid:conformance>", "<pdfaid:conformance>A</pdfaid:conformance>")
            pdf_writer.add_file_metadata(content.encode())