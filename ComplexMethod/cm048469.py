def action_generate_lot_line_vals(self, context_data, mode, first_lot, count, lot_text):
        if not context_data.get('default_product_id'):
            raise UserError(_("No product found to generate Serials/Lots for."))
        assert mode in ('generate', 'import')
        default_vals = {}

        def generate_lot_qty(quantity, qty_per_lot):
            if qty_per_lot <= 0:
                raise UserError(_("The quantity per lot should always be a positive value."))
            line_count = int(quantity // qty_per_lot)
            leftover = quantity % qty_per_lot
            qty_array = [qty_per_lot] * line_count
            if leftover:
                qty_array.append(leftover)
            return qty_array

        # Get default values
        def remove_prefix(text, prefix):
            if text.startswith(prefix):
                return text[len(prefix):]
            return text
        for key in context_data:
            if key.startswith('default_'):
                default_vals[remove_prefix(key, 'default_')] = context_data[key]

        if default_vals['tracking'] == 'lot' and mode == 'generate':
            lot_qties = generate_lot_qty(default_vals['quantity'], count)
        else:
            lot_qties = [1] * count

        if mode == 'generate':
            lot_names = self.env['stock.lot'].generate_lot_names(first_lot, len(lot_qties))
        elif mode == 'import':
            lot_names = self.split_lots(lot_text)
            lot_qties = [1] * len(lot_names)

        vals_list = []
        loc_dest = self.env['stock.location'].browse(default_vals['location_dest_id'])
        product = self.env['product.product'].browse(default_vals['product_id'])
        for lot, qty in zip(lot_names, lot_qties):
            if not lot.get('quantity'):
                lot['quantity'] = qty
            putaway_loc_dest = loc_dest._get_putaway_strategy(product, lot['quantity'])
            vals_list.append({**default_vals,
                             **lot,
                             'location_dest_id': putaway_loc_dest.id,
                             'product_uom_id': default_vals.get('uom_id', product.uom_id.id),
                            })
        if default_vals.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(default_vals['picking_type_id'])
            if picking_type.use_existing_lots or context_data.get('force_lot_m2o'):
                self._create_lot_ids_from_move_line_vals(
                    vals_list, default_vals['product_id'], default_vals['company_id']
                )
        # format many2one values for webclient, id + display_name
        for values in vals_list:
            for key, value in values.items():
                if key in self.env['stock.move.line'] and isinstance(self.env['stock.move.line'][key], models.Model):
                    values[key] = {
                        'id': value,
                        'display_name': self.env['stock.move.line'][key].browse(value).display_name
                    }
        if product.lot_sequence_id and first_lot:
            current_sequence = product.lot_sequence_id._get_current_sequence()
            increment = product.lot_sequence_id.number_increment
            first_number = current_sequence.number_next_actual - increment
            final_number = first_number
            # Since the value might have been incremented by the "New" button of the "Generate Serial Numbers" wizard
            # we need to consider both the decremented and the current value of the sequence
            if first_lot == product.lot_sequence_id.get_next_char(first_number):
                final_number = first_number + len(lot_qties)
            elif first_lot == product.lot_sequence_id.get_next_char(first_number + increment):
                final_number = first_number + increment + len(lot_qties)
            if first_number != final_number:
                current_sequence.sudo().write({'number_next_actual': final_number})
        return vals_list