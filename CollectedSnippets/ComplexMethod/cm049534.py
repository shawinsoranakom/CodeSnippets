def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        """Override to add and fill headers, footers and product documents to the sale quotation."""
        result = super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)
        if self._get_report(report_ref).report_name != 'sale.report_saleorder':
            return result

        ICP = self.env['ir.config_parameter'].sudo()
        always_include = str2bool(ICP.get_param('sale.always_include_selected_documents'))
        orders = self.env['sale.order'].browse(res_ids)

        for order in orders:
            if (
                (order.state != 'sale' or always_include)
                and (initial_stream := result.get(order.id, {}).get('stream'))
            ):
                quotation_documents = order.quotation_document_ids
                headers = quotation_documents.filtered(lambda doc: doc.document_type == 'header')
                footers = quotation_documents - headers
                has_product_document = any(line.product_document_ids for line in order.order_line)

                if not headers and not has_product_document and not footers:
                    continue

                form_fields_values_mapping = {}
                writer = PdfFileWriter()

                self_with_order_context = self.with_context(
                    use_babel=True, lang=order._get_lang() or self.env.user.lang
                )

                if headers:
                    for header in headers:
                        prefix = f'quotation_document_id_{header.id}__'
                        self_with_order_context._update_mapping_and_add_pages_to_writer(
                            writer, header, form_fields_values_mapping, prefix, order
                        )
                if has_product_document:
                    for line in order.order_line:
                        for doc in line.product_document_ids:
                            # Use both the id of the line and the doc as variants could use the same
                            # document.
                            prefix = f'sol_id_{line.id}_product_document_id_{doc.id}__'
                            self_with_order_context._update_mapping_and_add_pages_to_writer(
                                writer, doc, form_fields_values_mapping, prefix, order, line
                            )
                self._add_pages_to_writer(writer, initial_stream.getvalue())
                if footers:
                    for footer in footers:
                        prefix = f'quotation_document_id_{footer.id}__'
                        self_with_order_context._update_mapping_and_add_pages_to_writer(
                            writer, footer, form_fields_values_mapping, prefix, order
                        )
                pdf.fill_form_fields_pdf(writer, form_fields=form_fields_values_mapping)
                with io.BytesIO() as _buffer:
                    writer.write(_buffer)
                    stream = io.BytesIO(_buffer.getvalue())
                result[order.id].update({'stream': stream})

        return result