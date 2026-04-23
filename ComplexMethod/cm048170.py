def _apply_grid(self):
        """Apply the given list of changed matrix cells to the current SO."""
        if self.grid and self.grid_update:
            grid = json.loads(self.grid)
            product_template = self.env['product.template'].browse(grid['product_template_id'])
            dirty_cells = grid['changes']
            Attrib = self.env['product.template.attribute.value']
            default_so_line_vals = {}
            new_lines = []
            for cell in dirty_cells:
                combination = Attrib.browse(cell['ptav_ids'])
                no_variant_attribute_values = combination - combination._without_no_variant_attributes()

                # create or find product variant from combination
                product = product_template._create_product_variant(combination)
                order_lines = self.order_line.filtered(
                    lambda line: line.product_id.id == product.id
                    and line.product_no_variant_attribute_value_ids.ids == no_variant_attribute_values.ids
                    and not line.combo_item_id
                )

                # if product variant already exist in order lines
                old_qty = sum(order_lines.mapped('product_uom_qty'))
                qty = cell['qty']
                diff = qty - old_qty

                if not diff:
                    continue

                # TODO keep qty check? cannot be 0 because we only get cell changes ...
                if order_lines:
                    if qty == 0:
                        if self.state in ['draft', 'sent']:
                            # Remove lines if qty was set to 0 in matrix
                            # only if SO state = draft/sent
                            self.order_line -= order_lines
                        else:
                            order_lines.update({'product_uom_qty': 0.0})
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
                            raise ValidationError(_("You cannot change the quantity of a product present in multiple sale lines."))
                        else:
                            order_lines[0].product_uom_qty = qty
                            # If we want to support multiple lines edition:
                            # removal of other lines.
                            # For now, an error is raised instead
                            # if len(order_lines) > 1:
                            #     # Remove 1+ lines
                            #     self.order_line -= order_lines[1:]
                else:
                    if not default_so_line_vals:
                        OrderLine = self.env['sale.order.line']
                        default_so_line_vals = OrderLine.default_get(OrderLine._fields.keys())
                    last_sequence = self.order_line[-1:].sequence
                    if last_sequence:
                        default_so_line_vals['sequence'] = last_sequence
                    new_lines.append((0, 0, dict(
                        default_so_line_vals,
                        product_id=product.id,
                        product_uom_qty=qty,
                        product_no_variant_attribute_value_ids=no_variant_attribute_values.ids)
                    ))
            if new_lines:
                # Add new SO lines
                self.update(dict(order_line=new_lines))