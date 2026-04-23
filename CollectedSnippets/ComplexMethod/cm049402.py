def _apply_grid(self):
        if self.grid and self.grid_update:
            grid = json.loads(self.grid)
            product_template = self.env['product.template'].browse(grid['product_template_id'])
            product_ids = set()
            dirty_cells = grid['changes']
            Attrib = self.env['product.template.attribute.value']
            default_po_line_vals = {}
            new_lines = []
            for cell in dirty_cells:
                combination = Attrib.browse(cell['ptav_ids'])
                no_variant_attribute_values = combination - combination._without_no_variant_attributes()

                # create or find product variant from combination
                product = product_template._create_product_variant(combination)
                # TODO replace the check on product_id by a first check on the ptavs and pnavs?
                # and only create/require variant after no line has been found ???
                order_lines = self.order_line.filtered(lambda line: (line._origin or line).product_id == product and (line._origin or line).product_no_variant_attribute_value_ids == no_variant_attribute_values)

                # if product variant already exist in order lines
                old_qty = sum(order_lines.mapped('product_qty'))
                qty = cell['qty']
                diff = qty - old_qty

                if not diff:
                    continue

                product_ids.add(product.id)

                if order_lines:
                    if qty == 0:
                        if self.state in ['draft', 'sent']:
                            # Remove lines if qty was set to 0 in matrix
                            # only if PO state = draft/sent
                            self.order_line -= order_lines
                        else:
                            order_lines.update({'product_qty': 0.0})
                    else:
                        """
                        When there are multiple lines for same product and its quantity was changed in the matrix,
                        An error is raised.

                        A 'good' strategy would be to:
                            * Sets the quantity of the first found line to the cell value
                            * Remove the other lines.

                        But this would remove all business logic linked to the other lines...
                        Therefore, it only raises an Error for now.
                        """
                        if len(order_lines) > 1:
                            raise ValidationError(_("You cannot change the quantity of a product present in multiple purchase lines."))
                        else:
                            order_lines[0].product_qty = qty
                            # If we want to support multiple lines edition:
                            # removal of other lines.
                            # For now, an error is raised instead
                            # if len(order_lines) > 1:
                            #     # Remove 1+ lines
                            #     self.order_line -= order_lines[1:]
                else:
                    if not default_po_line_vals:
                        OrderLine = self.env['purchase.order.line']
                        default_po_line_vals = OrderLine.default_get(OrderLine._fields.keys())
                    last_sequence = self.order_line[-1:].sequence
                    if last_sequence:
                        default_po_line_vals['sequence'] = last_sequence
                    new_lines.append((0, 0, dict(
                        default_po_line_vals,
                        product_id=product.id,
                        product_qty=qty,
                        product_no_variant_attribute_value_ids=no_variant_attribute_values.ids)
                    ))
            if product_ids:
                if new_lines:
                    # Add new PO lines
                    self.update(dict(order_line=new_lines))

                # Recompute prices for new/modified lines:
                for line in self.order_line.filtered(lambda line: line.product_id.id in product_ids):
                    line._product_id_change()