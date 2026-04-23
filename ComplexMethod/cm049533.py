def _add_basic_mapped_form_fields(self):
        mapped_form_fields = {
            'quotation_document': {
                "amount_total": "amount_total",
                "amount_untaxed": "amount_untaxed",
                "client_order_ref": "client_order_ref",
                "delivery_date": "commitment_date",
                "order_date": "date_order",
                "name": "name",
                "partner_id__name": "partner_id.name",
                "user_id__email": "user_id.login",
                "user_id__name": "user_id.name",
                "validity_date": "validity_date",
            },
            'product_document': {
                "amount_total": "order_id.amount_total",
                "amount_untaxed": "order_id.amount_untaxed",
                "client_order_ref": "order_id.client_order_ref",
                "delivery_date": "order_id.commitment_date",
                "description": "name",
                "discount": "discount",
                "name": "order_id.name",
                "partner_id__name": "order_partner_id.name",
                "price_unit": "price_unit",
                "product_sale_price": "product_id.lst_price",
                "quantity": "product_uom_qty",
                "tax_excl_price": "price_subtotal",
                "tax_incl_price": "price_total",
                "taxes": "tax_ids",
                "uom": "product_uom_id.name",
                "user_id__name": "salesman_id.name",
                "validity_date": "order_id.validity_date",
            },
        }
        quote_doc = list(mapped_form_fields['quotation_document'])
        product_doc = list(mapped_form_fields['product_document'])
        existing_mapping = self.env['sale.pdf.form.field'].search([
            '|',
            '&', ('document_type', '=', 'quotation_document'), ('name', 'in', quote_doc),
            '&', ('document_type', '=', 'product_document'), ('name', 'in', product_doc)
        ])
        if existing_mapping:
            form_fields_to_add = {
                doc_type: {
                    name: path for name, path in mapped_form_fields[doc_type].items()
                    if not existing_mapping.filtered(
                        lambda ff: ff.document_type == doc_type and ff.name == name
                    )
                } for doc_type, mapping in mapped_form_fields.items()
            }
        else:
            form_fields_to_add = mapped_form_fields
        self.env['sale.pdf.form.field'].create([
            {'name': name, 'document_type': doc_type, 'path': path}
            for doc_type, mapping in form_fields_to_add.items()
            for name, path in mapping.items()
        ])