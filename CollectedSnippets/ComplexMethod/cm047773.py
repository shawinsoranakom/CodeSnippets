def _parse_serial_numbers(self):
        self.ensure_one()
        if not self.serial_numbers:
            raise UserError(self.env._("There is no serial numbers to apply."))
        lots = list(filter(lambda serial_number: len(serial_number.strip()) > 0, self.serial_numbers.split('\n'))) if self.serial_numbers else []
        if not lots:
            raise UserError(self.env._("No valid serial numbers provided."))
        existing_lots = self.env['stock.lot'].search([
            '|', ('company_id', '=', False), ('company_id', '=', self.production_id.company_id.id),
            ('product_id', '=', self.production_id.product_id.id),
            ('name', 'in', lots),
        ])
        existing_lot_names = existing_lots.mapped('name')
        new_lots_vals = []
        sequence = self.production_id.product_id.lot_sequence_id
        for lot_name in sorted(lots):
            if lot_name in existing_lot_names:
                continue
            if sequence and lot_name == sequence.get_next_char(sequence.number_next_actual):
                sequence.sudo().number_next_actual += 1
            new_lots_vals.append({
                'name': lot_name,
                'product_id': self.production_id.product_id.id,
            })
        new_lots = self.env['stock.lot'].create(new_lots_vals)
        return existing_lots + new_lots