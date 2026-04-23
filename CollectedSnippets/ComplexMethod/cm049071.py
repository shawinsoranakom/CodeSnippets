def _run_average_batch(self, at_date=None, lot=None, force_recompute=False):
        std_price_by_product_id = {}
        value_by_product_id = {}
        quantity_by_product_id = {}
        date_by_product_id = {}

        if not at_date and not force_recompute:
            std_price_by_product_id = {p.id: p.standard_price for p in self}
            value_by_product_id = {p.id: p.qty_available * std_price_by_product_id.get(p.id, 0) for p in self}
            return std_price_by_product_id, value_by_product_id

        moves_domain = Domain([
            ('product_id', 'in', self._as_query()),
            ('company_id', '=', self.env.company.id),
            '|', '|', ('is_in', '=', True), ('is_dropship', '=', True), ('is_out', '=', True)
        ])
        if lot:
            moves_domain &= Domain([
                ('move_line_ids.lot_id', 'in', lot.id),
            ])
        if at_date:
            moves_domain &= Domain([
                ('date', '<=', at_date),
            ])

        last_manual_value_by_product = self._get_last_product_value(at_date, lot=lot)
        oldest_manual_value = min(pv.date for pv in last_manual_value_by_product.values()) if last_manual_value_by_product else False
        if oldest_manual_value and self.env['product.product'].concat(*last_manual_value_by_product.keys()) == self:
            moves_domain &= Domain([('date', '>=', oldest_manual_value)])

        product_ids_by_manual_value_date = defaultdict(list)
        if not lot:
            for manual_value in last_manual_value_by_product.values():
                product_ids_by_manual_value_date[manual_value.date].append(manual_value.product_id.id)

        for manual_value in last_manual_value_by_product.values():
            product = manual_value.product_id
            if lot:
                quantity = lot.with_context(to_date=manual_value.date, skip_in_progress=True).product_qty
            else:
                quantity = product.with_prefetch(product_ids_by_manual_value_date[manual_value.date]).with_context(to_date=manual_value.date).qty_available

            std_price_by_product_id[product.id] = manual_value.value
            quantity_by_product_id[product.id] = quantity
            value_by_product_id[product.id] = manual_value.value * quantity
            date_by_product_id[product.id] = manual_value.date

        self.env['product.value'].invalidate_model()  # Avoid keeping too many records in cache

        moves = self.env['stock.move'].search_fetch(
            moves_domain,
            field_names=['id'],
            order='product_id, date, id'
        )
        # PERF avoid memoryerror
        move_fields = ['date', 'is_dropship', 'is_in', 'is_out', 'location_dest_id', 'location_id', 'move_line_ids', 'picked', 'value', 'product_id']
        move_line_fields = ['company_id', 'location_id', 'location_dest_id', 'lot_id', 'owner_id', 'picked', 'quantity_product_uom']

        product, valuation_from_date = False, False
        batch_size = 50000

        move_ids_by_product = defaultdict(list)
        # Limit the memory usage since it's possible to have millions of stock.move
        for moves_batch in split_every(batch_size, moves.ids):
            moves_batch = self.env['stock.move'].browse(moves_batch)
            moves_batch.fetch(['product_id', 'date'])

            for move in moves_batch:
                if move.product_id != product:
                    product = move.product_id
                    valuation_from_date = date_by_product_id.get(product.id)
                if valuation_from_date and move.date <= valuation_from_date:
                    continue
                move_ids_by_product[product].append(move.id)

            self.env['stock.move'].invalidate_model()

        for product, move_ids in move_ids_by_product.items():
            product_moves = self.env['stock.move'].browse(move_ids)

            first_move = product_moves[0]
            quantity = quantity_by_product_id.get(product.id, 0)
            average_cost = std_price_by_product_id.get(product.id, first_move.value / first_move._get_valued_qty() if first_move._get_valued_qty() else 0)
            value = value_by_product_id.get(product.id, 0)

            for moves_batch in split_every(batch_size, product_moves.ids):
                moves_batch = self.env['stock.move'].browse(moves_batch)
                moves_batch.fetch(move_fields)
                moves_batch.move_line_ids.fetch(move_line_fields)
                for move in moves_batch:
                    if move.is_in or move.is_dropship:
                        in_qty = move._get_valued_qty()
                        in_value = move.value
                        if at_date or move.is_dropship:
                            in_value = move._get_value(at_date=at_date, forced_std_price=average_cost)
                        if lot:
                            lot_qty = move._get_valued_qty(lot)
                            in_value = (in_value * lot_qty / in_qty) if in_qty else 0
                            in_qty = lot_qty
                        previous_qty = quantity
                        quantity += in_qty
                        # Regular case, value from accumulation
                        if previous_qty > 0:
                            value += in_value
                            average_cost = value / quantity
                        # From negative quantity case, value from last_in
                        elif previous_qty <= 0:
                            average_cost = in_value / in_qty if in_qty else average_cost
                            value = average_cost * quantity
                    if move.is_out or move.is_dropship:
                        out_qty = move._get_valued_qty()
                        out_value = out_qty * average_cost
                        if lot:
                            lot_qty = move._get_valued_qty(lot)
                            out_value = (out_value * lot_qty / out_qty) if out_qty else 0
                            out_qty = lot_qty
                        value -= out_value
                        quantity -= out_qty

                self.env['stock.move'].invalidate_model()  # Avoid keeping too many records in cache
                self.env['stock.move.line'].invalidate_model()

            std_price_by_product_id[product.id] = average_cost
            value_by_product_id[product.id] = value

        return std_price_by_product_id, value_by_product_id