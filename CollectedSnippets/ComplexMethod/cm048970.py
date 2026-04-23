def _is_auto_waveable(self):
        self.ensure_one()
        if not self.picking_id \
           or (self.picking_id.state != 'assigned' or self.product_uom_id.is_zero(self.quantity)) and not self.env.context.get('skip_auto_waveable')  \
           or self.batch_id.is_wave \
           or not self.picking_type_id._is_auto_wave_grouped() \
           or (self.picking_type_id.wave_group_by_category and self.product_id.categ_id not in self.picking_type_id.wave_category_ids):  # noqa: SIM103
            return False
        return True