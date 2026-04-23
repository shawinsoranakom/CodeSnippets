def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type == 'pdf' and download and invoice_sudo.state == 'posted':
            # Download the official attachment(s) or a Pro Forma invoice
            docs_data = invoice_sudo._get_invoice_legal_documents_all(allow_fallback=True)
            if len(docs_data) == 1:
                headers = self._get_http_headers(invoice_sudo, report_type, docs_data[0]['content'], download)
                return request.make_response(docs_data[0]['content'], list(headers.items()))
            else:
                filename = invoice_sudo._get_invoice_report_filename(extension='zip')
                zip_content = _build_zip_from_data(docs_data)
                headers = _get_headers(filename, 'zip', zip_content)
                return request.make_response(zip_content, headers)

        elif report_type in ('html', 'pdf', 'text'):
            has_generated_invoice = bool(invoice_sudo.invoice_pdf_report_id)
            request.update_context(proforma_invoice=not has_generated_invoice)
            # If the partner's language is RTL, set the context language to match, ensuring the report shows the correct text direction.
            partner_lang = invoice_sudo.partner_id.lang
            if partner_lang and request.env['res.lang']._get_data(code=partner_lang).direction == 'rtl':
                request.update_context(lang=partner_lang)
            # Use the template set on the related partner if there is.
            # This is not perfect as the invoice can still have been computed with another template, but it's a slight fix/imp for stable.
            pdf_report_name = invoice_sudo.partner_id.invoice_template_pdf_report_id.report_name or 'account.account_invoices'
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref=pdf_report_name, download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        return request.render("account.portal_invoice_page", values)