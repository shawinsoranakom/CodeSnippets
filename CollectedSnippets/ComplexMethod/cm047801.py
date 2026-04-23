def action_generate_serial(self, workorder=False):
        self.ensure_one()
        if self.product_tracking == 'lot':
            if self.lot_producing_ids:
                raise UserError(_("You cannot set more than 1 lot per product"))
            self.lot_producing_ids = [Command.create(self._prepare_stock_lot_values())]
            if self.picking_type_id.auto_print_generated_mrp_lot:
                return self._autoprint_generated_lot(self.lot_producing_ids[-1])
        elif self.product_tracking == 'serial':
            if self.product_qty == 1 and not self.lot_producing_ids:
                self.lot_producing_ids = [Command.create(self._prepare_stock_lot_values())]
                self.qty_producing = 1
                (workorder or self).set_qty_producing()
                if self.picking_type_id.auto_print_generated_mrp_lot:
                    return self._autoprint_generated_lot(self.lot_producing_ids[-1])
                return
            action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_assign_serial_numbers")
            action['context'] = {
                'default_production_id': self.id,
            }
            if workorder:
                action['context']['default_workorder_id'] = workorder.id
            return action