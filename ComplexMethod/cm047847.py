def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom):
        date_planned = self._get_date_planned(bom, values)
        date_deadline = values.get('date_deadline') or date_planned + relativedelta(days=bom.produce_delay)
        picking_type = bom.picking_type_id or self.picking_type_id
        mo_values = {
            'origin': origin,
            'product_id': product_id.id,
            'product_description_variants': values.get('product_description_variants'),
            'never_product_template_attribute_value_ids': values.get('never_product_template_attribute_value_ids'),
            'product_qty': product_uom._compute_quantity(product_qty, bom.product_uom_id) if bom else product_qty,
            'product_uom_id': bom.product_uom_id.id if bom else product_uom.id,
            'location_src_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id or location_dest_id.id,
            'location_final_id': location_dest_id.id,
            'bom_id': bom.id,
            'date_deadline': date_deadline,
            'date_start': date_planned,
            'reference_ids': [Command.set(values.get('reference_ids', self.env['stock.reference']).ids)],
            'propagate_cancel': self.propagate_cancel,
            'orderpoint_id': values.get('orderpoint_id', False) and values.get('orderpoint_id').id,
            'picking_type_id': picking_type.id or values['warehouse_id'].manu_type_id.id,
            'company_id': company_id.id,
            'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
            'user_id': False,
        }
        if self.location_dest_from_rule:
            mo_values['location_dest_id'] = self.location_dest_id.id
        return mo_values