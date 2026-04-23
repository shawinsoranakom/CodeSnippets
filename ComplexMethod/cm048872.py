def _compute_qty_to_deliver(self):
        """The inventory widget should now be visible in more cases if the product is consumable."""
        super(SaleOrderLine, self)._compute_qty_to_deliver()
        for line in self:
            # Hide the widget for kits since forecast doesn't support them.
            boms = self.env['mrp.bom']
            if line.state == 'sale':
                boms = line.move_ids.mapped('bom_line_id.bom_id')
            elif line.state in ['draft', 'sent'] and line.product_id:
                boms = boms._bom_find(line.product_id, company_id=line.company_id.id, bom_type='phantom')[line.product_id]
            relevant_bom = boms.filtered(lambda b: b.type == 'phantom' and
                    (b.product_id == line.product_id or
                    (b.product_tmpl_id == line.product_id.product_tmpl_id and not b.product_id)))
            if relevant_bom:
                line.display_qty_widget = False
                continue
            if line.state == 'draft' and line.product_type == 'consu':
                components = line.product_id.get_components()
                if components and components != [line.product_id.id]:
                    line.display_qty_widget = True