def _compute_estimated_shipping_capacity(self):
        for batch in self:
            estimated_shipping_weight = 0
            estimated_shipping_volume = 0
            done_package_ids = set()
            # packs
            for pack in batch.move_line_ids.result_package_id:
                p_type = pack.package_type_id
                if pack.shipping_weight:
                    # shipping_weight was computed, so base_weight should be included.
                    estimated_shipping_weight += pack.shipping_weight
                    done_package_ids.add(pack.id)
                elif p_type:
                    estimated_shipping_weight += p_type.base_weight or 0
                    estimated_shipping_volume += (p_type.packaging_length * p_type.width * p_type.height) / 1000.0**3
            # move without packs
            for move_line in batch.picking_ids.move_ids.move_line_ids:
                if move_line.result_package_id.id in done_package_ids:
                    continue
                estimated_shipping_weight += move_line.product_id.weight * move_line.quantity_product_uom
                estimated_shipping_volume += move_line.product_id.volume * move_line.quantity_product_uom
            batch.estimated_shipping_weight = estimated_shipping_weight
            batch.estimated_shipping_volume = estimated_shipping_volume