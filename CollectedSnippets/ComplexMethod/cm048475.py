def _generate_serial_move_line_commands(self, field_data, location_dest_id=False, origin_move_line=None):
        """Return a list of commands to update the move lines (write on
        existing ones or create new ones).
        Called when user want to create and assign multiple serial numbers in
        one time (using the button/wizard or copy-paste a list in the field).

        :param field_data: A list containing dict with at least `lot_name` and `quantity`
        :type field_data: list
        :param origin_move_line: A move line to duplicate the value from, empty record by default
        :type origin_move_line: record of :class:`stock.move.line`
        :return: A list of commands to create/update :class:`stock.move.line`
        :rtype: list
        """
        self.ensure_one()
        origin_move_line = origin_move_line or self.env['stock.move.line']
        loc_dest = origin_move_line.location_dest_id or location_dest_id
        move_line_vals = {
            'picking_id': self.picking_id.id,
            'location_id': self.location_id.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
        }
        # Select the right move lines depending of the picking type's configuration.
        move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)

        if origin_move_line:
            # Copies `owner_id` and `package_id` if new move lines are created from an existing one.
            move_line_vals.update({
                'owner_id': origin_move_line.owner_id.id,
                'package_id': origin_move_line.package_id.id,
            })

        move_lines_commands = []
        qty_by_location = defaultdict(float)
        for command_vals in field_data:
            quantity = command_vals['quantity']
            # We write the lot name on an existing move line (if we have still one)...
            if move_lines:
                move_lines_commands.append(Command.update(move_lines[0].id, command_vals))
                qty_by_location[move_lines[0].location_dest_id.id] += quantity
                move_lines = move_lines[1:]
            # ... or create a new move line with the serial name.
            else:
                loc = loc_dest or self.location_dest_id._get_putaway_strategy(self.product_id, quantity=quantity, additional_qty=qty_by_location)
                new_move_line_vals = {
                    **move_line_vals,
                    **command_vals,
                    'location_dest_id': loc.id
                }
                move_lines_commands.append(Command.create(new_move_line_vals))
                qty_by_location[loc.id] += quantity
        return move_lines_commands