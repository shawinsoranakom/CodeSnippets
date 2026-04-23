def _get_picking_type_update_values(self):
        data = super(StockWarehouse, self)._get_picking_type_update_values()
        data.update({
            'pbm_type_id': {
                'active': self.manufacture_to_resupply and self.manufacture_steps in ('pbm', 'pbm_sam') and self.active,
                'barcode': self.code.replace(" ", "").upper() + "PC",
            },
            'sam_type_id': {
                'active': self.manufacture_to_resupply and self.manufacture_steps == 'pbm_sam' and self.active,
                'barcode': self.code.replace(" ", "").upper() + "SFP",
            },
            'manu_type_id': {
                'active': self.manufacture_to_resupply and self.active,
                'barcode': self.code.replace(" ", "").upper() + "MANUF",
                'default_location_src_id': self.manufacture_steps in ('pbm', 'pbm_sam') and self.pbm_loc_id.id or self.lot_stock_id.id,
                'default_location_dest_id': self.manufacture_steps == 'pbm_sam' and self.sam_loc_id.id or self.lot_stock_id.id,
            },
        })
        return data