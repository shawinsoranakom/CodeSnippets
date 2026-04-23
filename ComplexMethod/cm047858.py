def _get_report_values(self, docids, data=None):
        docs = []
        for bom_id in docids:
            bom = self.env['mrp.bom'].browse(bom_id)
            if not bom:
                continue
            variant = data.get('variant')
            candidates = variant and self.env['product.product'].browse(int(variant)) or bom.product_id or bom.product_tmpl_id.product_variant_ids
            quantity = float(data.get('quantity', bom.product_qty))
            if data.get('warehouse_id'):
                self = self.with_context(warehouse_id=int(data.get('warehouse_id')))  # noqa: PLW0642
            for product_variant_id in candidates.ids:
                docs.append(self._get_pdf_doc(bom_id, data, quantity, product_variant_id))
            if not candidates:
                docs.append(self._get_pdf_doc(bom_id, data, quantity))
        return {
            'doc_ids': docids,
            'doc_model': 'mrp.bom',
            'docs': docs,
        }