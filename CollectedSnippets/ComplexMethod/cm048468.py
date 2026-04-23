def _create_lot_ids_from_move_line_vals(self, vals_list, product_id, company_id=False):
        """ This method will search or create the lot_id from the lot_name and set it in the vals_list
        """
        lot_names = [vals['lot_name'] for vals in vals_list if vals.get('lot_name')]
        lot_ids = self.env['stock.lot'].search([
            ('product_id', '=', product_id),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('name', 'in', lot_names),
        ])
        lot_id_names = set(lot_ids.mapped('name'))
        lot_names = [lot_name for lot_name in lot_names if lot_name not in lot_id_names]  # lot_names not found to create
        lots_to_create_vals = [
            {'product_id': product_id, 'name': lot_name}
            for lot_name in lot_names
        ]
        lot_ids |= self.env['stock.lot'].create(lots_to_create_vals)

        lot_id_by_name = {lot.name: lot.id for lot in lot_ids}
        for vals in vals_list:
            lot_name = vals.get('lot_name', None)
            if not lot_name:
                continue
            vals['lot_id'] = lot_id_by_name[lot_name]
            vals['lot_name'] = False