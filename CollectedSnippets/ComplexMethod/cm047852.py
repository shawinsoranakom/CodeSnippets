def create(self, vals_list):
        """ Enforce consistent values (i.e. match _get_move_raw_values/_get_move_finished_values) for:
        - Manually added components/byproducts specifically values we can't set via view with "default_"
        - Moves from a copied MO
        - Backorders
        """
        if self.env.context.get('force_manual_consumption'):
            for vals in vals_list:
                if 'quantity' in vals:
                    vals['manual_consumption'] = True
                vals['picked'] = True
        mo_id_to_mo = defaultdict(lambda: self.env['mrp.production'])
        product_id_to_product = defaultdict(lambda: self.env['product.product'])
        for values in vals_list:
            mo_id = values.get('raw_material_production_id', False) or values.get('production_id', False)
            location_dest = self.env['stock.location'].browse(values.get('location_dest_id'))
            if mo_id and location_dest.usage != 'inventory':
                mo = mo_id_to_mo[mo_id]
                if not mo:
                    mo = mo.browse(mo_id)
                    mo_id_to_mo[mo_id] = mo
                values['origin'] = mo._get_origin()
                values['propagate_cancel'] = mo.propagate_cancel
                values['reference_ids'] = mo.reference_ids.ids
                values['production_group_id'] = mo.production_group_id.id
                if values.get('raw_material_production_id', False):
                    product = product_id_to_product[values['product_id']]
                    if not product:
                        product = product.browse(values['product_id'])
                    product_id_to_product[values['product_id']] = product
                    values['location_dest_id'] = mo.production_location_id.id
                    if not values.get('location_id'):
                        values['location_id'] = mo.location_src_id.id
                    if mo.state in ['progress', 'to_close'] and mo.qty_producing > 0:
                        values['picked'] = True
                    continue
                # produced products + byproducts
                values['location_id'] = mo.production_location_id.id
                values['date'] = mo.date_finished
                values['date_deadline'] = mo.date_deadline
                if not values.get('location_dest_id'):
                    values['location_dest_id'] = mo.location_dest_id.id
                if not values.get('location_final_id'):
                    values['location_final_id'] = mo.warehouse_id.lot_stock_id.id
        return super().create(vals_list)