def _get_picking_type_update_values(self):
        """ Return values in order to update the existing picking type when the
        warehouse's delivery_steps or reception_steps are modify.
        """
        input_loc, output_loc = self._get_input_output_locations(self.reception_steps, self.delivery_steps)
        return {
            'in_type_id': {
                'default_location_dest_id': input_loc.id,
                'barcode': self.code.replace(" ", "").upper() + "IN",
            },
            'out_type_id': {
                'default_location_src_id': output_loc.id,
                'barcode': self.code.replace(" ", "").upper() + "OUT",
            },
            'pick_type_id': {
                'active': self.delivery_steps != 'ship_only' and self.active,
                'default_location_dest_id': output_loc.id if self.delivery_steps == 'pick_ship' else self.wh_pack_stock_loc_id.id,
                'barcode': self.code.replace(" ", "").upper() + "PICK",
            },
            'pack_type_id': {
                'active': self.delivery_steps == 'pick_pack_ship' and self.active,
                'default_location_dest_id': output_loc.id,
                'barcode': self.code.replace(" ", "").upper() + "PACK",
            },
            'qc_type_id': {
                'active': self.reception_steps == 'three_steps' and self.active,
                'barcode': self.code.replace(" ", "").upper() + "QC",
            },
            'store_type_id': {
                'active': self.reception_steps != 'one_step' and self.active,
                'default_location_src_id': input_loc.id if self.reception_steps == 'two_steps' else self.wh_qc_stock_loc_id.id,
                'barcode': self.code.replace(" ", "").upper() + "STOR",
            },
            'int_type_id': {
                'barcode': self.code.replace(" ", "").upper() + "INT",
            },
            'xdock_type_id': {
                'active': self.reception_steps != 'one_step' and self.delivery_steps != 'ship_only' and self.active,
                'barcode': self.code.replace(" ", "").upper() + "XD",
            }
        }