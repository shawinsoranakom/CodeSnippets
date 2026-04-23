def change_prod_qty(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit')
        for wizard in self:
            production = wizard.mo_id
            old_production_qty = production.product_qty
            new_production_qty = wizard.product_qty

            factor = new_production_qty / old_production_qty
            update_info = production._update_raw_moves(factor)
            documents = {}
            for move, old_qty, new_qty in update_info:
                iterate_key = production._get_document_iterate_key(move)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents({move: (new_qty, old_qty)}, iterate_key, 'UP')
                    for key, value in document.items():
                        if documents.get(key):
                            documents[key] += [value]
                        else:
                            documents[key] = [value]
            production._log_manufacture_exception(documents)
            self._update_finished_moves(production, new_production_qty, old_production_qty)
            production.write({'product_qty': new_production_qty})
            if not production.product_uom_id.is_zero(production.qty_producing) and not production.workorder_ids:
                production.qty_producing = new_production_qty
                production._set_qty_producing()

            for wo in production.workorder_ids:
                operation = wo.operation_id
                wo.duration_expected = wo._get_duration_expected(ratio=new_production_qty / old_production_qty)
                quantity = wo.qty_production - wo.qty_produced
                if production.product_id.tracking == 'serial':
                    quantity = 1.0 if not float_is_zero(quantity, precision_digits=precision) else 0.0
                else:
                    quantity = quantity if (quantity > 0 and not float_is_zero(quantity, precision_digits=precision)) else 0
                wo._update_qty_producing(quantity)
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                if wo.qty_produced == wo.qty_production and wo.state == 'progress':
                    wo.state = 'done'
                # assign moves; last operation receive all unassigned moves
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_line_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})

        # run scheduler for moves forecasted to not have enough in stock
        self.mo_id.filtered(lambda mo: mo.state in ['confirmed', 'progress']).move_raw_ids._trigger_scheduler()

        return {}