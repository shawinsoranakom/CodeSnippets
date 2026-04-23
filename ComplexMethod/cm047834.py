def explode(self, product, quantity, picking_type=False, never_attribute_values=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        self = self.with_context(bom_cost_share_cache=self.env.context.get('bom_cost_share_cache') or {})  # noqa: PLW0642
        product_ids = set()
        product_boms = {}
        def update_product_boms():
            products = self.env['product.product'].browse(product_ids)
            product_boms.update(self._bom_find(products, picking_type=picking_type or self.picking_type_id,
                company_id=self.company_id.id, bom_type='phantom'))
            # Set missing keys to default value
            for product in products:
                product_boms.setdefault(product, self.env['mrp.bom'])

        boms_done = [(self, self.env['mrp.bom.line']._prepare_bom_done_values(quantity, product, quantity, []))]
        lines_done = []

        bom_lines = []
        for bom_line in self.bom_line_ids:
            product_id = bom_line.product_id
            bom_lines.append((bom_line, product, quantity, False))
            product_ids.add(product_id.id)
        update_product_boms()
        product_ids.clear()
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product, never_attribute_values):
                continue

            line_quantity = current_qty * current_line.product_qty
            if current_line.product_id not in product_boms:
                update_product_boms()
                product_ids.clear()
            bom = product_boms.get(current_line.product_id)
            if bom:
                converted_line_quantity = current_line.product_uom_id._compute_quantity(
                    line_quantity / bom.product_qty, bom.product_uom_id, round=False
                )
                bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids] + bom_lines
                for bom_line in bom.bom_line_ids:
                    if bom_line.product_id not in product_boms:
                        product_ids.add(bom_line.product_id.id)
                boms_done.append((bom, current_line._prepare_bom_done_values(converted_line_quantity, current_product, quantity, boms_done)))
            else:
                # We round up here because the user expects that if he has to consume a little more, the whole UOM unit
                # should be consumed.
                line_quantity = current_line.product_uom_id.round(line_quantity, rounding_method='UP')
                lines_done.append((current_line, current_line._prepare_line_done_values(line_quantity, current_product, quantity, parent_line, boms_done)))

        lines_done = self._round_last_line_done(lines_done)
        return boms_done, lines_done