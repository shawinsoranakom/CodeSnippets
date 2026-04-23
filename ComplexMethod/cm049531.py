def get_update_included_pdf_params(self):
        if not self:
            return {
                'headers': {},
                'files': {},
                'footers': {},
            }
        self.ensure_one()
        existing_mapping = (
            self.customizable_pdf_form_fields
            and json.loads(self.customizable_pdf_form_fields)
        ) or {}

        available_docs = self.available_quotation_document_ids | self.quotation_document_ids
        headers_available = available_docs.filtered(
            lambda doc: doc.document_type == 'header'
        )
        footers_available = available_docs.filtered(
            lambda doc: doc.document_type == 'footer'
        )
        selected_documents = self.quotation_document_ids
        selected_headers = selected_documents.filtered(lambda doc: doc.document_type == 'header')
        selected_footers = selected_documents - selected_headers
        lines_params = []
        for line in self.order_line:
            if line.available_product_document_ids:
                lines_params.append({
                    'name': _("Product") + " > " + line.name.splitlines()[0],
                    'id': line.id,
                    'files': [{
                        'name': doc.name.rstrip('.pdf'),
                        'id': doc.id,
                        'is_selected': doc in line.sudo().product_document_ids, # User should be
                        # able to access all product documents even without sales access
                        'custom_form_fields': [{
                            'name': custom_form_field.name,
                            'value': existing_mapping.get('line', {}).get(str(line.id), {}).get(
                                str(doc.id), {}
                            ).get('custom_form_fields', {}).get(custom_form_field.name, ""),
                        } for custom_form_field in doc.form_field_ids.filtered(
                            lambda ff: not ff.path
                        )],
                    } for doc in line.available_product_document_ids]
                })
        dialog_params = {
            'headers': {'name': _("Header"), 'files': [{
                'id': header.id,
                'name': header.name,
                'is_selected': header in selected_headers,
                'custom_form_fields': [{
                    'name': custom_form_field.name,
                    'value': existing_mapping.get('header', {}).get(str(header.id), {}).get(
                        'custom_form_fields', {}
                    ).get(custom_form_field.name, ""),
                } for custom_form_field in header.form_field_ids.filtered(lambda ff: not ff.path)],
            } for header in headers_available]},
            'lines': lines_params,
            'footers': {'name': _("Footer"), 'files': [{
                'id': footer.id,
                'name': footer.name,
                'is_selected': footer in selected_footers,
                'custom_form_fields': [{
                    'name': custom_form_field.name,
                    'value': existing_mapping.get('footer', {}).get(str(footer.id), {}).get(
                        'custom_form_fields', {}
                    ).get(custom_form_field.name, ""),
                } for custom_form_field in footer.form_field_ids.filtered(lambda ff: not ff.path)],
            } for footer in footers_available]},
        }
        return dialog_params