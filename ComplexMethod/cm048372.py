def _get_orderpoint_action(self):
        """Create manual orderpoints for missing product in each warehouses. It also removes
        orderpoints that have been replenish. In order to do it:
        - It uses the report.stock.quantity to find missing quantity per product/warehouse
        - It checks if orderpoint already exist to refill this location.
        - It checks if it exists other sources (e.g RFQ) tha refill the warehouse.
        - It creates the orderpoints for missing quantity that were not refill by an upper option.

        return replenish report ir.actions.act_window
        """
        def is_parent_path_in(resupply_loc, path_dict, record_loc):
            return record_loc and resupply_loc.parent_path in path_dict.get(record_loc, '')

        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_orderpoint_replenish")
        action['context'] = self.env.context
        # Search also with archived ones to avoid to trigger product_location_check SQL constraints later
        # It means that when there will be a archived orderpoint on a location + product, the replenishment
        # report won't take in account this location + product and it won't create any manual orderpoint
        # In master: the active field should be remove
        orderpoints = self.env['stock.warehouse.orderpoint'].with_context(active_test=False).search([])
        # Remove previous automatically created orderpoint that has been refilled.
        orderpoints_removed = orderpoints._unlink_processed_orderpoints()
        orderpoints = orderpoints - orderpoints_removed
        if self.env.context.get('force_orderpoint_recompute', False):
            orderpoints._compute_qty_to_order_computed()
            orderpoints._compute_deadline_date()
        to_refill = defaultdict(float)
        all_product_ids = self._get_orderpoint_products()
        all_replenish_location_ids = self._get_orderpoint_locations()
        ploc_per_day = defaultdict(set)
        # For each replenish location get products with negative virtual_available aka forecast

        Move = self.env['stock.move'].with_context(active_test=False)
        Quant = self.env['stock.quant'].with_context(active_test=False)
        domain_quant, domain_move_in_loc, domain_move_out_loc = all_product_ids._get_domain_locations_new(all_replenish_location_ids.ids)
        domain_state = Domain('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))
        domain_product = Domain('product_id', 'in', all_product_ids.ids)

        domain_quant = Domain.AND((domain_product, domain_quant))
        domain_move_in = Domain.AND((domain_product, domain_state, domain_move_in_loc))
        domain_move_out = Domain.AND((domain_product, domain_state, domain_move_out_loc))

        moves_in = defaultdict(list)
        for item in Move._read_group(domain_move_in, ['product_id', 'location_dest_id', 'location_final_id'], ['product_qty:sum']):
            moves_in[item[0]].append((item[1], item[2], item[3]))

        moves_out = defaultdict(list)
        for item in Move._read_group(domain_move_out, ['product_id', 'location_id'], ['product_qty:sum']):
            moves_out[item[0]].append((item[1], item[2]))

        quants = defaultdict(list)
        for item in Quant._read_group(domain_quant, ['product_id', 'location_id'], ['quantity:sum']):
            quants[item[0]].append((item[1], item[2]))

        path = {loc: loc.parent_path for loc in self.env['stock.location'].with_context(active_test=False).search([('id', 'child_of', all_replenish_location_ids.ids)])}
        for loc in all_replenish_location_ids:
            for product in all_product_ids:
                qty_available = sum(q[1] for q in quants.get(product, [(0, 0)]) if is_parent_path_in(loc, path, q[0]))
                incoming_qty = sum(m[2] for m in moves_in.get(product, [(0, 0, 0)]) if is_parent_path_in(loc, path, m[0]) or is_parent_path_in(loc, path, m[1]))
                outgoing_qty = sum(m[1] for m in moves_out.get(product, [(0, 0)]) if is_parent_path_in(loc, path, m[0]))
                if product.uom_id.compare(qty_available + incoming_qty - outgoing_qty, 0) < 0:
                    # group product by lead_days and location in order to read virtual_available
                    # in batch
                    rules = product._get_rules_from_location(loc)
                    lead_days = rules.with_context(bypass_delay_description=True)._get_lead_days(product)[0]
                    ploc_per_day[lead_days['total_delay'] + lead_days['horizon_time'], loc].add(product.id)

        # recompute virtual_available with lead days
        today = fields.Datetime.now().replace(hour=23, minute=59, second=59)
        product_ids = set()
        location_ids = set()
        for (days, loc), prod_ids in ploc_per_day.items():
            products = self.env['product.product'].browse(prod_ids)
            qties = products.with_context(
                location=loc.id,
                to_date=today + relativedelta.relativedelta(days=days)
            ).read(['virtual_available'])
            for (product, qty) in zip(products, qties):
                if product.uom_id.compare(qty['virtual_available'], 0) < 0:
                    to_refill[(qty['id'], loc.id)] = qty['virtual_available']
                    product_ids.add(qty['id'])
                    location_ids.add(loc.id)
            products.invalidate_recordset()
        if not to_refill:
            return action

        # Remove incoming quantity from other origin than moves (e.g RFQ)
        product_ids = list(product_ids)
        location_ids = list(location_ids)
        qty_by_product_loc = self.env['product.product'].browse(product_ids)._get_quantity_in_progress(location_ids=location_ids)[0]
        rounding = self.env['decimal.precision'].precision_get('Product Unit')
        # Group orderpoint by product-location
        orderpoint_by_product_location = self.env['stock.warehouse.orderpoint']._read_group(
            [('id', 'in', orderpoints.ids), ('product_id', 'in', product_ids)],
            ['product_id', 'location_id'],
            ['id:recordset'])
        orderpoint_by_product_location = {
            (product.id, location.id): orderpoint.qty_to_order
            for product, location, orderpoint in orderpoint_by_product_location
        }
        for (product, location), product_qty in to_refill.items():
            qty_in_progress = qty_by_product_loc.get((product, location)) or 0.0
            qty_in_progress += orderpoint_by_product_location.get((product, location), 0.0)
            # Add qty to order for other orderpoint under this location.
            if not qty_in_progress:
                continue
            to_refill[(product, location)] = product_qty + qty_in_progress
        to_refill = {k: v for k, v in to_refill.items() if float_compare(
            v, 0.0, precision_digits=rounding) < 0.0}

        # With archived ones to avoid `product_location_check` SQL constraints
        orderpoint_by_product_location = self.env['stock.warehouse.orderpoint'].with_context(active_test=False)._read_group(
            [('id', 'in', orderpoints.ids), ('product_id', 'in', product_ids)],
            ['product_id', 'location_id'],
            ['id:recordset'])
        orderpoint_by_product_location = {
            (product.id, location.id): orderpoint
            for product, location, orderpoint in orderpoint_by_product_location
        }

        orderpoint_values_list = []
        for (product, location_id), product_qty in to_refill.items():
            orderpoint = orderpoint_by_product_location.get((product, location_id))
            if orderpoint:
                orderpoint.qty_forecast += product_qty
            else:
                orderpoint_values = self.env['stock.warehouse.orderpoint']._get_orderpoint_values(product, location_id)
                location = self.env['stock.location'].browse(location_id)
                orderpoint_values.update({
                    'name': _('Replenishment Report'),
                    'warehouse_id': location.warehouse_id.id or self.env['stock.warehouse'].search([('company_id', '=', location.company_id.id)], limit=1).id,
                    'company_id': location.company_id.id,
                })
                orderpoint_values_list.append(orderpoint_values)

        orderpoints = self.env['stock.warehouse.orderpoint'].with_user(SUPERUSER_ID).create(orderpoint_values_list)
        return action