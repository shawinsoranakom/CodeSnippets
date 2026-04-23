def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        # Custom behavior for 'account.report_original_vendor_bill'.
        if self._get_report(report_ref).report_name != 'account.report_original_vendor_bill':
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)

        invoices = self.env['account.move'].browse(res_ids)
        original_attachments = invoices.message_main_attachment_id
        if not original_attachments:
            raise UserError(_("No original purchase document could be found for any of the selected purchase documents."))

        collected_streams = OrderedDict()
        for invoice in invoices:
            attachment = self._prepare_local_attachments(invoice.message_main_attachment_id)
            if attachment:
                stream = pdf.to_pdf_stream(attachment)
                if stream:
                    record = self.env[attachment.res_model].browse(attachment.res_id)
                    try:
                        stream = pdf.add_banner(stream, record.name or '', logo=True)
                    except (ValueError, pdf.PdfReadError, TypeError, zlib_error, NotImplementedError, pdf.DependencyError, ArithmeticError):
                        record._message_log(body=_(
                            "There was an error when trying to add the banner to the original PDF.\n"
                            "Please make sure the source file is valid."
                        ))
                collected_streams[invoice.id] = {
                    'stream': stream,
                    'attachment': attachment,
                }
        return collected_streams