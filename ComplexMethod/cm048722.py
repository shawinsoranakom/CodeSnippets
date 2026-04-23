def _generate_invoice_documents(self, invoices_data, allow_fallback_pdf=False):
        """ Generate the invoice PDF and electronic documents.
        :param invoices_data:   The collected data for invoices so far.
        :param allow_fallback_pdf:  In case of error when generating the documents for invoices, generate a
                                    proforma PDF report instead.
        """
        for invoice, invoice_data in invoices_data.items():
            self._hook_invoice_document_before_pdf_report_render(invoice, invoice_data)
            invoice_data['blocking_error'] = invoice_data.get('error') \
                                             and not (allow_fallback_pdf and invoice_data.get('error_but_continue'))
            invoice_data['error_but_continue'] = allow_fallback_pdf and invoice_data.get('error_but_continue')

        invoices_data_web_service = {
            invoice: invoice_data
            for invoice, invoice_data in invoices_data.items()
            if not invoice_data.get('error')
        }
        if invoices_data_web_service:
            self._call_web_service_before_invoice_pdf_render(invoices_data_web_service)

        invoices_data_pdf = {
            invoice: invoice_data
            for invoice, invoice_data in invoices_data.items()
            if not invoice_data.get('error') or invoice_data.get('error_but_continue')
        }

        # Use batch to avoid memory error
        batch_size = self.env['ir.config_parameter'].sudo().get_param('account.pdf_generation_batch', '80')
        batches = []
        pdf_to_generate = {}
        for invoice, invoice_data in invoices_data_pdf.items():
            if not invoice_data.get('error') and not invoice.invoice_pdf_report_id:  # we don't regenerate pdf if it already exists
                pdf_to_generate[invoice] = invoice_data

                if (len(pdf_to_generate) > int(batch_size)):
                    batches.append(pdf_to_generate)
                    pdf_to_generate = {}

        if pdf_to_generate:
            batches.append(pdf_to_generate)

        for batch in batches:
            self._prepare_invoice_pdf_report(batch)

        for invoice, invoice_data in invoices_data_pdf.items():
            if not invoice_data.get('error') and not invoice.invoice_pdf_report_id:
                self._hook_invoice_document_after_pdf_report_render(invoice, invoice_data)

        # Cleanup the error if we don't want to block the regular pdf generation.
        if allow_fallback_pdf:
            invoices_data_pdf_error = {
                invoice: invoice_data
                for invoice, invoice_data in invoices_data.items()
                if invoice_data.get('pdf_attachment_values') and invoice_data.get('error')
            }
            if invoices_data_pdf_error:
                self._hook_if_errors(invoices_data_pdf_error, allow_raising=not allow_fallback_pdf)

        # Web-service after the PDF generation.
        invoices_data_web_service = {
            invoice: invoice_data
            for invoice, invoice_data in invoices_data.items()
            if not invoice_data.get('error')
        }
        if invoices_data_web_service:
            self._call_web_service_after_invoice_pdf_render(invoices_data_web_service)

        # Create and link the generated documents to the invoice if the web-service didn't failed.
        invoices_to_link = {
            invoice: invoice_data
            for invoice, invoice_data in invoices_data_web_service.items()
            if not invoice_data.get('error') or allow_fallback_pdf
        }
        self._link_invoice_documents(invoices_to_link)