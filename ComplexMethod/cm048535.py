def download_invoice_documents_filetype(self, invoices, filetype, allow_fallback=True):
        invoices.check_access('read')
        invoices.line_ids.check_access('read')
        docs_data = []
        for invoice in invoices:
            if filetype == 'all' and (doc_data := invoice._get_invoice_legal_documents_all(allow_fallback=allow_fallback)):
                docs_data += doc_data
            elif doc_data := invoice._get_invoice_legal_documents(filetype, allow_fallback=allow_fallback):
                if (errors := doc_data.get('errors')) and len(invoices) == 1:
                    raise UserError(_("Error while creating XML:\n- %s", '\n- '.join(errors)))
                docs_data.append(doc_data)
        if len(docs_data) == 1:
            doc_data = docs_data[0]
            headers = _get_headers(doc_data['filename'], doc_data['filetype'], doc_data['content'])
            return request.make_response(doc_data['content'], headers)
        if len(docs_data) > 1:
            zip_content = _build_zip_from_data(docs_data)
            headers = _get_headers(_('invoices') + '.zip', 'zip', zip_content)
            return request.make_response(zip_content, headers)