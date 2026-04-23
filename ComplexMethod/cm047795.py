def _change_producing(self):
        if self.state in ['draft', 'cancel'] or (self.state == 'done' and self.is_locked):
            return False
        if self.product_tracking == 'serial' and self.lot_producing_ids:
            self.qty_producing = len(self.lot_producing_ids)
        productions_bypass_qty_producting = self.filtered(lambda p: p.lot_producing_ids and p.product_tracking == 'lot' and p._origin and p._origin.qty_producing == p.qty_producing)
        # sudo needed for portal users
        (self - productions_bypass_qty_producting).sudo()._set_qty_producing(False)
        return True