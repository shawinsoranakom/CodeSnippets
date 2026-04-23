def _get_report_values(self, docids, data=None):
        ''' This report is flexibly designed to work with both individual and batch pickings.
        '''
        docs = self._get_docs(docids)
        doc_states = docs.mapped('state')
        # unsupported cases
        doc_types = self._get_doc_types()
        if not docs:
            msg = _("No %s selected or a delivery order selected", doc_types)
        elif 'done' in doc_states and len(set(doc_states)) > 1:
            docs = False
            msg = _("This report cannot be used for done and not done %s at the same time", doc_types)
        if not docs:
            return {'pickings': False, 'reason': msg}

        # incoming move qtys
        product_to_qty_draft = defaultdict(float)
        product_to_qty_to_assign = defaultdict(list)
        product_to_total_assigned = defaultdict(lambda: [0.0, []])

        # to support batch pickings we need to track the total already assigned
        move_ids = self._get_moves(docs)
        assigned_moves = move_ids.mapped('move_dest_ids')
        product_to_assigned_qty = defaultdict(float)
        for assigned in assigned_moves:
            product_to_assigned_qty[assigned.product_id] += assigned.product_qty

        for move in move_ids:
            move_quantity = (
                move.product_qty or
                move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id, rounding_method='HALF-UP')
            )
            qty_already_assigned = 0
            if move.move_dest_ids:
                qty_already_assigned = min(product_to_assigned_qty[move.product_id], move_quantity)
                product_to_assigned_qty[move.product_id] -= qty_already_assigned
            if qty_already_assigned:
                product_to_total_assigned[move.product_id][0] += qty_already_assigned
                product_to_total_assigned[move.product_id][1].append(move.id)
            if move_quantity != qty_already_assigned:
                if move.state == 'draft':
                    product_to_qty_draft[move.product_id] += move_quantity - qty_already_assigned
                else:
                    quantity_to_assign = move_quantity
                    product_to_qty_to_assign[move.product_id].append((quantity_to_assign - qty_already_assigned, move))

        # only match for non-mto moves in same warehouse
        warehouse = docs[0].picking_type_id.warehouse_id
        wh_location_ids = self.env['stock.location']._search([('id', 'child_of', warehouse.view_location_id.id), ('usage', '!=', 'supplier')])

        allowed_states = ['confirmed', 'partially_available', 'waiting']
        if 'done' in doc_states:
            # only done moves are allowed to be assigned to already reserved moves
            allowed_states += ['assigned']

        outs = self.env['stock.move'].search(
            [
                ('state', 'in', allowed_states),
                ('product_qty', '>', 0),
                ('location_id', 'in', wh_location_ids),
                ('move_orig_ids', '=', False),
                ('product_id', 'in',
                    [p.id for p in list(product_to_qty_to_assign.keys()) + list(product_to_qty_draft.keys())]),
            ] + self._get_extra_domain(docs),
            order='reservation_date, priority desc, date, id')

        products_to_outs = defaultdict(list)
        for out in outs:
            products_to_outs[out.product_id].append(out)

        sources_to_lines = defaultdict(list)  # group by source so we can print them together
        # show potential moves that can be assigned
        for product_id, outs in products_to_outs.items():
            for out in outs:
                # we expect len(source) = 2 when picking + origin [e.g. SO] and len() = 1 otherwise [e.g. MO]
                source = (out._get_source_document(),)
                if not source:
                    continue
                if out.picking_id and source[0] != out.picking_id:
                    source = (out.picking_id, source[0])

                qty_to_reserve = out.product_qty
                product_uom = out.product_id.uom_id
                if 'done' not in doc_states and out.state == 'partially_available':
                    qty_to_reserve -= out.product_uom._compute_quantity(out.quantity, product_uom)
                moves_in_ids = []
                quantity = 0
                for move_in_qty, move_in in product_to_qty_to_assign[out.product_id]:
                    moves_in_ids.append(move_in.id)
                    if product_uom.compare(quantity + move_in_qty, qty_to_reserve) <= 0:
                        qty_to_add = move_in_qty
                        move_in_qty = 0
                    else:
                        qty_to_add = qty_to_reserve - quantity
                        move_in_qty -= qty_to_add
                    quantity += qty_to_add
                    if move_in_qty:
                        product_to_qty_to_assign[out.product_id][0] = (move_in_qty, move_in)
                    else:
                        product_to_qty_to_assign[out.product_id] = product_to_qty_to_assign[out.product_id][1:]
                    if product_uom.compare(qty_to_reserve, quantity) == 0:
                        break

                if not product_uom.is_zero(quantity):
                    sources_to_lines[source].append(self._prepare_report_line(quantity, product_id, out, source[0], move_ins=self.env['stock.move'].browse(moves_in_ids)))

                # draft qtys can be shown but not assigned
                qty_expected = product_to_qty_draft.get(product_id, 0)
                if product_uom.compare(qty_to_reserve, quantity) > 0 and not product_uom.is_zero(qty_expected):
                    to_expect = min(qty_expected, qty_to_reserve - quantity)
                    sources_to_lines[source].append(self._prepare_report_line(to_expect, product_id, out, source[0], is_qty_assignable=False))
                    product_to_qty_draft[product_id] -= to_expect

        # show already assigned moves
        for product_id, qty_and_ins in product_to_total_assigned.items():
            total_assigned = qty_and_ins[0]
            moves_in = self.env['stock.move'].browse(qty_and_ins[1])
            out_moves = moves_in.move_dest_ids

            for out_move in out_moves:
                if out_move.product_id.uom_id.is_zero(total_assigned):
                    # it is possible there are different in moves linked to the same out moves due to batch
                    # => we guess as to which outs correspond to this report...
                    continue
                source = (out_move._get_source_document(),)
                if not source:
                    continue
                if out_move.picking_id and source[0] != out_move.picking_id:
                    source = (out_move.picking_id, source[0])
                qty_assigned = min(total_assigned, out_move.product_qty)
                sources_to_lines[source].append(
                    self._prepare_report_line(qty_assigned, product_id, out_move, source[0], is_assigned=True, move_ins=moves_in))

        # dates aren't auto-formatted when printed in report :(
        sources_to_formatted_scheduled_date = defaultdict(list)
        for source in sources_to_lines:
            sources_to_formatted_scheduled_date[source] = self._get_formatted_scheduled_date(source[0])

        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': self._get_doc_model(),
            'sources_to_lines': sources_to_lines,
            'precision': self.env['decimal.precision'].precision_get('Product Unit'),
            'docs': docs,
            'sources_to_formatted_scheduled_date': sources_to_formatted_scheduled_date,
        }