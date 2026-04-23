def _get_report_lines(self, product_template_ids, product_ids, wh_location_ids, wh_stock_location, read=True):

        def _get_out_move_reserved_data(out, linked_moves, used_reserved_moves, currents, wh_stock_location, wh_stock_sub_location_ids):
            reserved_out = 0
            # the move to show when qty is reserved
            reserved_move = self.env['stock.move']
            for move in linked_moves:
                if move.state not in ('partially_available', 'assigned'):
                    continue
                # count reserved stock.
                reserved = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                # check if the move reserved qty was counted before (happens if multiple outs share pick/pack)
                reserved = min(reserved - used_reserved_moves[move], out.product_qty)
                if reserved and not reserved_move:
                    reserved_move = move
                # add to reserved line data
                reserved_out += reserved
                used_reserved_moves[move] += reserved
                # any sublocation qties needs to be reserved to the main stock location qty as well
                if move.location_id.id in wh_stock_sub_location_ids:
                    currents[out.product_id.id, wh_stock_location.id] -= reserved
                currents[(out.product_id.id, move.location_id.id)] -= reserved
                if move.product_id.uom_id.compare(reserved_out, out.product_qty) >= 0:
                    break

            return {
                'reserved': reserved_out,
                'reserved_move': reserved_move,
                'linked_moves': linked_moves,
            }

        def _get_out_move_taken_from_stock_data(out, currents, reserved_data, wh_stock_location, wh_stock_sub_location_ids):
            reserved_out = reserved_data['reserved']
            demand_out = out.product_qty - reserved_out
            linked_moves = reserved_data['linked_moves']
            taken_from_stock_out = 0
            for move in linked_moves:
                if move.state in ('draft', 'cancel', 'assigned', 'done'):
                    continue
                reserved = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                demand = max(move.product_qty - reserved, 0)
                # to make sure we don't demand more than the out (useful when same pick/pack goes to multiple out)
                demand = min(demand, demand_out)
                if move.product_id.uom_id.is_zero(demand):
                    continue
                # check available qty for move if chained, move available is what was move by orig moves
                if move.move_orig_ids:
                    move_in_qty = sum(move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('quantity'))
                    sibling_moves = (move.move_orig_ids.move_dest_ids - move)
                    move_out_qty = sum(sibling_moves.filtered(lambda m: m.state == 'done').mapped('quantity'))
                    move_available_qty = move_in_qty - move_out_qty - reserved
                else:
                    move_available_qty = currents[(out.product_id.id, move.location_id.id)]
                # count taken from stock, but avoid taking more than whats in stock in case of move origs,
                # this can happen if stock adjustment is done after orig moves are done
                taken_from_stock = min(demand, move_available_qty, currents[(out.product_id.id, move.location_id.id)])
                if taken_from_stock > 0:
                    # any sublocation qties needs to be removed to the main stock location qty as well
                    if move.location_id.id in wh_stock_sub_location_ids:
                        currents[out.product_id.id, wh_stock_location.id] -= taken_from_stock
                    currents[(out.product_id.id, move.location_id.id)] -= taken_from_stock
                    taken_from_stock_out += taken_from_stock
                demand_out -= taken_from_stock
            return {
                'taken_from_stock': taken_from_stock_out,
            }

        def _reconcile_out_with_ins(lines, out, ins, demand, product_rounding, in_id_to_in_data, ins_per_product, dest_ids_to_in_ids, read=True):
            ins_to_remove = []
            for in_id in ins:
                in_data = in_id_to_in_data[in_id]
                if float_is_zero(in_data['qty'], precision_rounding=product_rounding):
                    ins_to_remove.append(in_id)
                    continue
                taken_from_in = min(demand, in_data['qty'])
                demand -= taken_from_in
                lines.append(self._prepare_report_line(taken_from_in, move_in=in_data['move'], move_out=out, read=read))
                in_data['qty'] -= taken_from_in
                if in_data['qty'] <= 0:
                    ins_to_remove.append(in_id)
                if float_is_zero(demand, precision_rounding=product_rounding):
                    break

            for in_id in ins_to_remove:
                in_data = in_id_to_in_data[in_id]
                product_id = in_data['move'].product_id.id
                for dest in in_data['move_dests']:
                    dest_ids_to_in_ids[dest].remove(in_id)
                ins_per_product[product_id].remove(in_id)
            return demand

        in_domain, out_domain = self._move_confirmed_domain(
            product_template_ids, product_ids, wh_location_ids
        )
        past_domain = [('reservation_date', '<=', date.today())]
        future_domain = ['|', ('reservation_date', '>', date.today()), ('reservation_date', '=', False)]

        past_outs = self.env['stock.move'].search(Domain.AND([out_domain, past_domain]), order='priority desc, date, id')
        future_outs = self.env['stock.move'].search(Domain.AND([out_domain, future_domain]), order='reservation_date, priority desc, date, id')

        outs = past_outs | future_outs

        ins = self.env['stock.move'].search(in_domain, order='priority desc, date, id')
        # Prewarm cache with rollups
        outs._rollup_move_origs_fetch()
        ins._rollup_move_dests_fetch()

        linked_moves_per_out = {}
        ins_ids = set(ins._ids)
        for out in outs:
            linked_move_ids = out._rollup_move_origs() - ins_ids
            linked_moves_per_out[out] = self.env['stock.move'].browse(linked_move_ids)

        # Gather all linked moves
        all_linked_move_ids = {
            _id for _ids in linked_moves_per_out.values() for _id in _ids._ids
        }
        all_linked_moves = self.env['stock.move'].browse(all_linked_move_ids)

        # Prewarm cache with sibling move's state/quantity
        all_linked_moves.fetch(['move_orig_ids'])
        all_linked_moves.move_orig_ids.fetch(['move_dest_ids'])
        all_linked_moves.move_orig_ids.move_dest_ids.fetch(['state', 'quantity'])

        # Share prefetch ids among all linked moves for performance
        for out, linked_moves in linked_moves_per_out.items():
            linked_moves_per_out[out] = linked_moves.with_prefetch(
                all_linked_moves._prefetch_ids
            )

        outs_per_product = defaultdict(list)
        for out in outs:
            outs_per_product[out.product_id.id].append(out)

        dest_ids_to_in_ids, in_id_to_in_data = defaultdict(OrderedSet), {}
        ins_per_product = defaultdict(OrderedSet)
        for in_ in ins:
            in_id_to_in_data[in_.id] = {
                'qty': in_.product_qty,
                'move': in_,
                'move_dests': in_._rollup_move_dests(),
            }
            product_id = in_.product_id.id
            ins_per_product[product_id].add(in_.id)
            for dest in in_id_to_in_data[in_.id]['move_dests']:
                dest_ids_to_in_ids[dest].add(in_.id)

        qties = self.env['stock.quant']._read_group(
            self._get_quant_domain(wh_location_ids, outs.product_id | self._get_products(product_template_ids, product_ids)),
            ['product_id', 'location_id'], ['quantity:sum']
        )
        wh_stock_sub_location_ids = set(
            (wh_stock_location.search([('id', 'child_of', wh_stock_location.id)]) - wh_stock_location)._ids
        )
        currents = defaultdict(float)
        for product, location, quantity in qties:
            location_id = location.id
            # any sublocation qties will be added to the main stock location qty as well
            if location_id in wh_stock_sub_location_ids:
                currents[product.id, wh_stock_location.id] += quantity
            currents[(product.id, location_id)] += quantity
        moves_data = {}
        for out_moves in outs_per_product.values():
            # to handle multiple out wtih same in (ex: same pick/pack for 2 outs)
            used_reserved_moves = defaultdict(float)
            # for all out moves, check for linked moves and count reserved quantity
            for out in out_moves:
                moves_data[out] = _get_out_move_reserved_data(
                    out, linked_moves_per_out[out], used_reserved_moves, currents, wh_stock_location, wh_stock_sub_location_ids
                )
            # another loop to remove qty from current stock after reserved is counted for
            for out in out_moves:
                data = _get_out_move_taken_from_stock_data(out, currents, moves_data[out], wh_stock_location, wh_stock_sub_location_ids)
                moves_data[out].update(data)
        product_sum = defaultdict(float)
        for product_loc, quantity in currents.items():
            if product_loc[1] not in wh_stock_sub_location_ids:
                product_sum[product_loc[0]] += quantity
        lines = []
        for product in (ins | outs).product_id | self._get_products(product_template_ids, product_ids):
            lines_init_count = len(lines)
            product_rounding = product.uom_id.rounding
            unreconciled_outs = []
            # remaining stock
            free_stock = currents[product.id, wh_stock_location.id]
            transit_stock = product_sum[product.id] - free_stock
            # add report lines and see if remaining demand can be reconciled by unreservable stock or ins
            for out in outs_per_product[product.id]:
                reserved_out = moves_data[out].get('reserved')
                taken_from_stock_out = moves_data[out].get('taken_from_stock')
                reserved_move = moves_data[out].get('reserved_move')
                demand_out = out.product_qty
                # Reconcile with the reserved stock.
                if reserved_out > 0:
                    demand_out = max(demand_out - reserved_out, 0)
                    in_transit = bool(reserved_move.move_orig_ids)
                    lines.append(self._prepare_report_line(reserved_out, move_out=out, reserved_move=reserved_move, in_transit=in_transit, read=read))

                if float_is_zero(demand_out, precision_rounding=product_rounding):
                    continue

                # Reconcile with the current stock.
                if taken_from_stock_out > 0:
                    demand_out = max(demand_out - taken_from_stock_out, 0)
                    lines.append(self._prepare_report_line(taken_from_stock_out, move_out=out, read=read))

                if float_is_zero(demand_out, precision_rounding=product_rounding):
                    continue

                # Reconcile with unreservable stock, quantities that are in stock but not in correct location to reserve from (in transit)
                unreservable_qty = min(demand_out, transit_stock)
                if unreservable_qty > 0:
                    demand_out -= unreservable_qty
                    transit_stock -= unreservable_qty
                    lines.append(self._prepare_report_line(unreservable_qty, move_out=out, in_transit=True, read=read))

                if float_is_zero(demand_out, precision_rounding=product_rounding):
                    continue

                # Reconcile with the ins.
                demand_out = _reconcile_out_with_ins(lines, out, dest_ids_to_in_ids[out.id], demand_out, product_rounding, in_id_to_in_data, ins_per_product, dest_ids_to_in_ids, read=read)

                if not float_is_zero(demand_out, precision_rounding=product_rounding):
                    unreconciled_outs.append((demand_out, out))

            # Another pass, in case there are some ins linked to a dest move but that still have some quantity available
            for (demand, out) in unreconciled_outs:
                demand = _reconcile_out_with_ins(lines, out, ins_per_product[product.id], demand, product_rounding, in_id_to_in_data, ins_per_product, dest_ids_to_in_ids, read=read)
                if not float_is_zero(demand, precision_rounding=product_rounding):
                    # Not reconciled
                    lines.append(self._prepare_report_line(demand, move_out=out, replenishment_filled=False, read=read))
            # Stock in transit
            if not float_is_zero(transit_stock, precision_rounding=product_rounding):
                lines.append(self._prepare_report_line(transit_stock, product=product, in_transit=True, read=read))

            # Unused remaining stock.
            if not float_is_zero(free_stock, precision_rounding=product.uom_id.rounding) or lines_init_count == len(lines):
                lines += self._free_stock_lines(product, free_stock, moves_data, wh_location_ids, read)

            # In moves not used.
            for in_id in ins_per_product[product.id]:
                in_data = in_id_to_in_data[in_id]
                if float_is_zero(in_data['qty'], precision_rounding=product_rounding):
                    continue
                lines.append(self._prepare_report_line(in_data['qty'], move_in=in_data['move'], read=read))
        return lines