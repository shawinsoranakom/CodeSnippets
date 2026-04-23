def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('repair_id') or 'repair_line_type' not in vals:
                continue
            repair_id = self.env['repair.order'].browse([vals['repair_id']])
            vals['origin'] = repair_id.name
        moves = super().create(vals_list)
        repair_moves = self.env['stock.move']
        for move in moves:
            if not move.repair_id:
                continue
            move.reference_ids = [Command.link(r.id) for r in move.repair_id.reference_ids]
            move.picking_type_id = move.repair_id.picking_type_id.id
            repair_moves |= move
        no_repair_moves = moves - repair_moves
        draft_repair_moves = repair_moves.filtered(lambda m: m.state == 'draft' and m.repair_id.state in ('confirmed', 'under_repair'))
        other_repair_moves = repair_moves - draft_repair_moves
        draft_repair_moves._check_company()
        draft_repair_moves._adjust_procure_method(picking_type_code='repair_operation')
        res = draft_repair_moves._action_confirm()
        res._trigger_scheduler()
        confirmed_repair_moves = (res | other_repair_moves)
        confirmed_repair_moves._create_repair_sale_order_line()
        return (confirmed_repair_moves | no_repair_moves)