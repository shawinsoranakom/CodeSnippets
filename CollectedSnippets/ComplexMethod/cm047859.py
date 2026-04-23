def _get_report_data(self, bom_id, searchQty=0, searchVariant=False):
        lines = {}
        bom = self.env['mrp.bom'].browse(bom_id)
        bom_quantity = searchQty or bom.product_qty or 1
        bom_product_variants = {}
        bom_uom_name = ''

        if searchVariant:
            product = self.env['product.product'].browse(int(searchVariant))
        else:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id or bom.product_tmpl_id.with_context(active_test=False).product_variant_ids[:1]

        if bom:
            bom_uom_name = bom.product_uom_id.name

            # Get variants used for search
            if not bom.product_id:
                for variant in bom.product_tmpl_id.product_variant_ids:
                    bom_product_variants[variant.id] = variant.display_name

        if self.env.context.get('warehouse_id'):
            warehouse = self.env['stock.warehouse'].browse(self.env.context.get('warehouse_id'))
        else:
            warehouses = self.get_warehouses()
            warehouse = self.env['stock.warehouse'].browse(warehouses[0]['id']) if warehouses else self.env['stock.warehouse']

        lines = self._get_bom_data(bom, warehouse, product=product, line_qty=bom_quantity, level=0)
        return {
            'lines': lines,
            'variants': bom_product_variants,
            'bom_uom_name': bom_uom_name,
            'bom_qty': bom_quantity,
            'is_variant_applied': self.env.user.has_group('product.group_product_variant') and len(bom_product_variants) > 1,
            'is_uom_applied': self.env.user.has_group('uom.group_uom'),
            'precision': self.env['decimal.precision'].precision_get('Product Unit'),
        }