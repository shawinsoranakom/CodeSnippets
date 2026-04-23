def _add_myinvois_document_line_item_nodes(self, line_node, vals):
        self._add_document_line_item_nodes(line_node, vals)

        record = vals['base_line']['record']
        if record and record.name:
            line_name = record.name and record.name.replace('\n', ' ')
        else:
            line_name = vals['base_line']['line_name']
        if line_name:
            line_node['cac:Item']['cbc:Description']['_text'] = line_name
            if not line_node['cac:Item']['cbc:Name']['_text']:
                line_node['cac:Item']['cbc:Name']['_text'] = line_name

        # When the invoice is sent for the general public (refunding an order in a consolidated invoice/...) the item code
        # must be fixed to 004 (consolidated invoice) even if the product has something else set.
        myinvois_document = vals['myinvois_document']
        if myinvois_document._is_consolidated_invoice() or myinvois_document._is_consolidated_invoice_refund():
            class_code = '004'
        else:
            base_line = vals['base_line']
            class_code = base_line['record'].l10n_my_edi_classification_code or \
                         base_line['record'].product_id.product_tmpl_id.l10n_my_edi_classification_code

        if class_code:
            line_node['cac:Item']['cac:CommodityClassification'] = {
                'cbc:ItemClassificationCode': {
                    '_text': class_code,
                    'listID': 'CLASS',
                }
            }