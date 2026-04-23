def action_relocate_quants(self):
        self.ensure_one()
        lot_ids = self.quant_ids.lot_id
        product_ids = self.quant_ids.product_id

        if not self.dest_location_id and not self.dest_package_id:
            return
        self.quant_ids.action_clear_inventory_quantity()

        if self.is_partial_package and not self.dest_package_id:
            quants_to_unpack = self.quant_ids.filtered(lambda q: not all(sub_q in self.quant_ids.ids for sub_q in q.package_id.quant_ids.ids))
            quants_to_unpack.move_quants(location_dest_id=self.dest_location_id, message=self.message, unpack=True)
            self.quant_ids -= quants_to_unpack
        self.quant_ids.move_quants(location_dest_id=self.dest_location_id, package_dest_id=self.dest_package_id, message=self.message)

        if self.env.context.get('default_lot_id', False) and len(lot_ids) == 1:
            return lot_ids.action_lot_open_quants()
        elif self.env.context.get('single_product', False) and len(product_ids) == 1:
            return product_ids.action_open_quants()
        return self.quant_ids.with_context(always_show_loc=1).action_view_quants()