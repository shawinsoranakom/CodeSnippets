def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        # only to_date as to_date will correspond to qty_available
        original_value = to_date
        to_date = fields.Datetime.to_datetime(to_date)
        if (isinstance(original_value, date) and not isinstance(original_value, datetime)) or \
            (isinstance(original_value, str) and len(original_value) == 10):
            to_date = datetime.combine(to_date.date(), time.max)

        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
            domain_move_in += [('move_line_ids.lot_id', '=', lot_id)]
            domain_move_out += [('move_line_ids.lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if 'owners' in self.env.context:
            owners = self.env.context['owners']
            if owners:
                domain_quant += [('owner_id', 'in', self.env.context['owners'])]
            else:
                domain_quant += [('owner_id', '=', False)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
        if from_date:
            date_date_expected_domain_from = [('date', '>=', from_date)]
            domain_move_in += date_date_expected_domain_from
            domain_move_out += date_date_expected_domain_from
        if to_date:
            date_date_expected_domain_to = [('date', '<=', to_date)]
            domain_move_in += date_date_expected_domain_to
            domain_move_out += date_date_expected_domain_to
        Move = self.env['stock.move'].with_context(active_test=False)
        Quant = self.env['stock.quant'].with_context(active_test=False)
        domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
        domain_move_out_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
        moves_in_res = {product.id: product_qty for product, product_qty in Move._read_group(domain_move_in_todo, ['product_id'], ['product_qty:sum'])}
        moves_out_res = {product.id: product_qty for product, product_qty in Move._read_group(domain_move_out_todo, ['product_id'], ['product_qty:sum'])}
        quants_res = {product.id: (quantity, reserved_quantity) for product, quantity, reserved_quantity in Quant._read_group(domain_quant, ['product_id'], ['quantity:sum', 'reserved_quantity:sum'])}
        expired_unreserved_quants_res = {}
        if self.env.context.get('with_expiration'):
            max_date = self.env.context['to_date'] if self.env.context.get('to_date') else self.env.context['with_expiration']
            domain_quant += [('removal_date', '<=', max_date)]
            expired_unreserved_quants_res = {product.id: quantity - reserved_quantity for product, quantity, reserved_quantity in Quant._read_group(domain_quant, ['product_id'], ['quantity:sum', 'reserved_quantity:sum'])}
        moves_in_res_past = defaultdict(float)
        moves_out_res_past = defaultdict(float)
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            groupby = ['product_id', 'product_uom']
            for product, uom, quantity in Move._read_group(domain_move_in_done, groupby, ['quantity:sum']):
                moves_in_res_past[product.id] += uom._compute_quantity(quantity, product.uom_id)

            for product, uom, quantity in Move._read_group(domain_move_out_done, groupby, ['quantity:sum']):
                moves_out_res_past[product.id] += uom._compute_quantity(quantity, product.uom_id)

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            origin_product_id = product._origin.id
            product_id = product.id
            if not origin_product_id or (
                origin_product_id not in quants_res
                and origin_product_id not in moves_in_res
                and origin_product_id not in moves_out_res
                and origin_product_id not in moves_in_res_past
                and origin_product_id not in moves_out_res_past
                and origin_product_id not in expired_unreserved_quants_res
            ):
                res[product_id] = dict.fromkeys(
                    ['qty_available', 'free_qty', 'incoming_qty', 'outgoing_qty', 'virtual_available'],
                    0.0,
                )
                continue
            res[product_id] = {}
            if dates_in_the_past:
                qty_available = quants_res.get(origin_product_id, [0.0])[0] - moves_in_res_past.get(origin_product_id, 0.0) + moves_out_res_past.get(origin_product_id, 0.0)
            else:
                qty_available = quants_res.get(origin_product_id, [0.0])[0]
            reserved_quantity = quants_res.get(origin_product_id, [False, 0.0])[1]
            expired_unreserved_qty = expired_unreserved_quants_res.get(origin_product_id, 0.0)
            res[product_id]['qty_available'] = product.uom_id.round(qty_available)
            res[product_id]['free_qty'] = product.uom_id.round(qty_available - reserved_quantity - expired_unreserved_qty)
            res[product_id]['incoming_qty'] = product.uom_id.round(moves_in_res.get(origin_product_id, 0.0))
            res[product_id]['outgoing_qty'] = product.uom_id.round(moves_out_res.get(origin_product_id, 0.0))
            res[product_id]['virtual_available'] = product.uom_id.round(
                qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'] - expired_unreserved_qty,
            )

        return res