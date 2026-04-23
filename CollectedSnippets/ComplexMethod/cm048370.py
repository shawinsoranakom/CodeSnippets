def _compute_deadline_date(self):
        """ This function first checks if the qty_on_hand is less than the product_min_qty. If it is the case,
        the deadline_date is set to the current day. Afterwards if there are still orderpoints to compute,
        it retrieves all the outgoing and incoming moves until the lead_horizon_date and adds (or subtracts)
        them to the qty_on_hand. The first instance when the qty_on_hand dips below the product_min_qty is
        the deadline date. """
        self.fetch(['qty_on_hand'])
        critical_orderpoints = self.filtered(lambda o: o.qty_on_hand < o.product_min_qty)
        critical_orderpoints.deadline_date = fields.Date.today()
        orderpoints_to_compute = self - critical_orderpoints
        if not orderpoints_to_compute:
            return

        # We have to filter by company here in case of multi-company and because horizon_days is a company setting
        for company in orderpoints_to_compute.company_id:
            company_orderpoints = orderpoints_to_compute.filtered(lambda c: c.company_id == company)
            horizon_date = fields.Date.today() + relativedelta.relativedelta(days=company_orderpoints.get_horizon_days())
            _, domain_move_in, domain_move_out = company_orderpoints.product_id._get_domain_locations()
            domain_move_in = Domain.AND([
                [('product_id', 'in', company_orderpoints.product_id.ids)],
                [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))],
                domain_move_in,
                [('date', '<=', horizon_date)],
            ])
            domain_move_out = Domain.AND([
                [('product_id', '=', company_orderpoints.product_id.ids)],
                [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))],
                domain_move_out,
                [('date', '<=', horizon_date)],
            ])

            Move = self.env['stock.move'].with_context(active_test=False)
            incoming_moves_by_product_date = Move._read_group(domain_move_in, ['product_id', 'location_dest_id', 'date:day'], ['product_qty:sum'])
            outgoing_moves_by_product_date = Move._read_group(domain_move_out, ['product_id', 'location_id', 'date:day'], ['product_qty:sum'])

            moves_by_product_dict = {}
            for product, location, in_date, in_qty in incoming_moves_by_product_date:
                if not moves_by_product_dict.get((product.id, location.id)):
                    moves_by_product_dict[product.id, location.id] = defaultdict(float)
                moves_by_product_dict[product.id, location.id][in_date.date()] += in_qty
            for product, location, out_date, out_qty in outgoing_moves_by_product_date:
                if not moves_by_product_dict.get((product.id, location.id)):
                    moves_by_product_dict[product.id, location.id] = defaultdict(float)
                moves_by_product_dict[product.id, location.id][out_date.date()] -= out_qty

            for orderpoint in company_orderpoints:
                qty_on_hand_at_date = orderpoint.qty_on_hand
                tentative_deadline = horizon_date
                for move_date, move_qty in sorted(moves_by_product_dict.get((orderpoint.product_id.id, orderpoint.location_id.id), {}).items()):
                    qty_on_hand_at_date += move_qty
                    if qty_on_hand_at_date < orderpoint.product_min_qty:
                        tentative_deadline = move_date - relativedelta.relativedelta(days=orderpoint.lead_days)
                        break
                orderpoint.deadline_date = tentative_deadline if tentative_deadline < horizon_date else False