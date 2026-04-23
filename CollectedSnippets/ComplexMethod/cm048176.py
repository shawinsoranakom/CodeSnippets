def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        if len(self.order_id.reference_ids.move_ids.production_group_id) == 1:
            for re in res:
                re['production_group_id'] = self.order_id.reference_ids.move_ids.production_group_id.id
        sale_line_product = self._get_sale_order_line_product()
        if sale_line_product:
            bom = self.env['mrp.bom']._bom_find(self.env['product.product'].browse(sale_line_product.id), company_id=picking.company_id.id, bom_type='phantom')
            # Was a kit sold?
            bom_kit = bom.get(sale_line_product)
            if bom_kit:
                _dummy, bom_sub_lines = bom_kit.explode(sale_line_product, self.sale_line_id.product_uom_qty)
                bom_kit_component = {line['product_id'].id: line.id for line, _ in bom_sub_lines}
                # Find the sml for the kit component
                for vals in res:
                    if vals['product_id'] in bom_kit_component:
                        vals['bom_line_id'] = bom_kit_component[vals['product_id']]
        return res