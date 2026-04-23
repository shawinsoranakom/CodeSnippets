def _onchange_order_line(self):
        for index, line in enumerate(self.order_line):
            if line.display_type == 'line_subsection' and not line.parent_id:
                line.display_type = 'line_section'
            combo_item_lines = line._get_linked_lines().filtered('combo_item_id')
            if line.product_template_id.type != 'combo':
                if combo_item_lines:
                    # Delete any linked combo item lines if the line's product is no longer a combo
                    # product.
                    self.order_line = [
                        Command.delete(linked_line.id) for linked_line in combo_item_lines
                    ]
            elif line.selected_combo_items:
                selected_combo_items = json.loads(line.selected_combo_items)
                if (
                    selected_combo_items
                    and len(selected_combo_items) != len(line.product_template_id.sudo().combo_ids)
                ):
                    raise ValidationError(_(
                        "The number of selected combo items must match the number of available"
                        " combo choices."
                    ))

                # Delete any existing combo item lines.
                delete_commands = [Command.delete(linked_line.id) for linked_line in combo_item_lines]
                # Create a new combo item line for each selected combo item.
                create_commands = [Command.create({
                    'product_id': combo_item['product_id'],
                    'product_uom_qty': line.product_uom_qty,
                    'combo_item_id': combo_item['combo_item_id'],
                    'product_no_variant_attribute_value_ids': [
                        Command.set(combo_item['no_variant_attribute_value_ids'])
                    ],
                    'product_custom_attribute_value_ids': [Command.clear()] + [
                        Command.create(attribute_value)
                        for attribute_value in combo_item['product_custom_attribute_values']
                    ],
                    # Combo item lines should come directly after their combo product line.
                    'sequence': line.sequence + item_index + 1,
                    # If the linked line exists in DB, populate linked_line_id, otherwise populate
                    # linked_virtual_id.
                    'linked_line_id': line.id if line._origin else False,
                    'linked_virtual_id': line.virtual_id if not line._origin else False,
                }) for item_index, combo_item in enumerate(selected_combo_items)]
                # Shift any lines coming after the combo product line so that the combo item lines
                # come first.
                update_commands = [Command.update(
                    order_line.id,
                    {'sequence': order_line.sequence + len(selected_combo_items)},
                ) for order_line in self.order_line if order_line.sequence > line.sequence]

                # Clear `selected_combo_items` to avoid applying the same changes multiple times.
                line.selected_combo_items = False
                self.order_line = delete_commands + create_commands + update_commands
            elif (
                combo_item_lines
                # Only update the combo item lines if the line's combo choices haven't changed.
                and combo_item_lines.combo_item_id.combo_id == line.product_template_id.combo_ids
            ):
                combo_item_lines.update({
                    'product_uom_qty': line.product_uom_qty,
                    'discount': line.discount,
                })