def _push_apply(self):
        new_moves = []
        for move in self:
            new_move = self.env['stock.move']

            # if the move is a returned move, we don't want to check push rules, as returning a returned move is the only decent way
            # to receive goods without triggering the push rules again (which would duplicate chained operations)
            # first priority goes to the preferred routes defined on the move itself (e.g. coming from a SO line)
            warehouse_id = move.warehouse_id or move.picking_id.picking_type_id.warehouse_id

            StockRule = self.env['stock.rule']
            if move.location_dest_id.company_id not in self.env.companies:
                StockRule = self.env['stock.rule'].sudo()
                move = move.with_context(allowed_companies=self.env.user.company_ids.ids)
                warehouse_id = False

            related_packages = self.env['stock.package'].search_fetch([('id', 'parent_of', move.move_line_ids.result_package_id.ids)], ['package_type_id'])

            rule = StockRule._get_push_rule(move.product_id, move.location_dest_id, {
                'route_ids': move.route_ids | related_packages.package_type_id.route_ids, 'warehouse_id': warehouse_id, 'packaging_uom_id': move.packaging_uom_id,
            })

            excluded_rule_ids = []
            while (rule and rule.push_domain and not move.filtered_domain(literal_eval(rule.push_domain))):
                excluded_rule_ids.append(rule.id)
                rule = StockRule._get_push_rule(move.product_id, move.location_dest_id, {
                    'route_ids': move.route_ids | related_packages.package_type_id.route_ids, 'warehouse_id': warehouse_id, 'packaging_uom_id': move.packaging_uom_id,
                    'domain': [('id', 'not in', excluded_rule_ids)],
                })

            # Make sure it is not returning the return
            if rule and (not move.origin_returned_move_id or move.origin_returned_move_id.location_dest_id.id != rule.location_dest_id.id):
                new_move = rule._run_push(move) or new_move
                if new_move:
                    new_moves.append(new_move)

            move_to_propagate_ids = set()
            move_to_mts_ids = set()
            for m in move.move_dest_ids - new_move:
                if new_move and move.location_final_id and m.location_id == move.location_final_id:
                    move_to_propagate_ids.add(m.id)
                elif not m.location_id._child_of(move.location_dest_id):
                    move_to_mts_ids.add(m.id)
            self.env['stock.move'].browse(move_to_mts_ids)._break_mto_link(move)
            move.move_dest_ids = [Command.unlink(m_id) for m_id in move_to_propagate_ids]
            new_move.move_dest_ids = [Command.link(m_id) for m_id in move_to_propagate_ids]

        new_moves = self.env['stock.move'].concat(*new_moves)
        new_moves = new_moves.sudo()._action_confirm()

        return new_moves