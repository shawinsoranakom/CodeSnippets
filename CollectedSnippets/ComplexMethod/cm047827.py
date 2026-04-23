def button_finish(self):
        date_finished = fields.Datetime.now()
        all_vals_dict = defaultdict(lambda: self.env['mrp.workorder'])
        workorders_to_end = self.filtered(lambda workorder: workorder.state not in ('done', 'cancel'))
        operations = workorders_to_end.operation_id
        moves_to_pick = workorders_to_end.move_raw_ids.filtered(lambda move: not move.picked)
        moves_to_pick += workorders_to_end.production_id.move_byproduct_ids.filtered(lambda move: not move.picked and move.operation_id in operations)

        for move in moves_to_pick:
            production_id = move.raw_material_production_id or move.production_id
            if production_id.product_uom_id.is_zero(production_id.qty_producing):
                qty_available = production_id.product_qty
            else:
                qty_available = production_id.qty_producing
            new_qty = move.product_uom.round(qty_available * move.unit_factor)
            move._set_quantity_done(new_qty)

        moves_to_pick.picked = True
        workorders_to_end.end_all()
        for workorder in workorders_to_end:
            vals = {
                'qty_produced': workorder.qty_produced or workorder.qty_producing or workorder.qty_production,
                'state': 'done',
                'date_finished': date_finished,
                'costs_hour': workorder.workcenter_id.costs_hour
            }
            if not workorder.date_start or date_finished < workorder.date_start:
                vals['date_start'] = date_finished
            all_vals_dict[frozenset(vals.items())] |= workorder
        for frozen_vals, workorders in all_vals_dict.items():
            workorders.with_context(bypass_duration_calculation=True).write(dict(frozen_vals))
        return True