def _compute_forecast_information(self):
        """ Compute forecasted information of the related product by warehouse."""
        self.forecast_availability = False
        self.forecast_expected_date = False

        # Prefetch product info to avoid fetching all product fields
        self.product_id.fetch(['type', 'uom_id'])

        not_product_moves = self.filtered(lambda move: not move.product_id.is_storable)
        for move in not_product_moves:
            move.forecast_availability = move.product_qty

        product_moves = (self - not_product_moves)

        outgoing_unreserved_moves_per_warehouse = defaultdict(set)
        now = fields.Datetime.now()

        def key_virtual_available(move, incoming=False):
            warehouse_id = move.location_dest_id.warehouse_id.id if incoming else move.location_id.warehouse_id.id
            return warehouse_id, max(move.date or now, now)

        # Prefetch efficiently virtual_available for _is_consuming draft move.
        prefetch_virtual_available = defaultdict(set)
        virtual_available_dict = {}
        for move in product_moves:
            if move._is_consuming() and move.state == 'draft' or move.picking_code == 'internal':
                prefetch_virtual_available[key_virtual_available(move)].add(move.product_id.id)
            elif move.picking_type_id.code == 'incoming':
                prefetch_virtual_available[key_virtual_available(move, incoming=True)].add(move.product_id.id)
        for key_context, product_ids in prefetch_virtual_available.items():
            read_res = self.env['product.product'].browse(product_ids).with_context(warehouse_id=key_context[0], to_date=key_context[1]).read([
                'virtual_available',
                'free_qty',
            ])
            virtual_available_dict[key_context] = {res['id']: (res['virtual_available'], res['free_qty']) for res in read_res}

        for move in product_moves:
            if key_virtual_available(move) in virtual_available_dict and move.product_id.id in virtual_available_dict[key_virtual_available(move)]:
                free_qty = virtual_available_dict[key_virtual_available(move)][move.product_id.id][1]
            else:
                free_qty = 0.0
            if move.state == 'assigned':
                move.forecast_availability = move.product_uom._compute_quantity(
                    move.quantity, move.product_id.uom_id, rounding_method='HALF-UP')
                continue
            elif move.state == 'draft' and float_compare(free_qty, move.product_qty, precision_rounding=move.product_id.uom_id.rounding) >= 0:
                move.forecast_availability = free_qty
                continue
            if move._is_consuming():
                if move.state == 'draft':
                    free_qty = virtual_available_dict[key_virtual_available(move)][move.product_id.id][0]
                    if float_compare(free_qty, move.product_qty, precision_rounding=move.product_id.uom_id.rounding) >= 0:
                        move.forecast_availability = free_qty
                        continue
                    # for move _is_consuming and in draft -> the forecast_availability > 0 if in stock
                    move.forecast_availability = free_qty - move.product_qty
                elif move.state in ('waiting', 'confirmed', 'partially_available'):
                    outgoing_unreserved_moves_per_warehouse[move.location_id.warehouse_id].add(move.id)
            elif move.picking_type_id.code == 'internal':
                if float_compare(free_qty, move.product_qty, precision_rounding=move.product_id.uom_id.rounding) >= 0:
                    move.forecast_availability = free_qty
                    continue
            elif move.picking_type_id.code == 'incoming':
                forecast_availability = virtual_available_dict[key_virtual_available(move, incoming=True)][move.product_id.id][0]
                if move.state == 'draft':
                    forecast_availability += move.product_qty
                move.forecast_availability = forecast_availability

        for warehouse, moves_ids in outgoing_unreserved_moves_per_warehouse.items():
            if not warehouse:  # No prediction possible if no warehouse.
                continue
            moves_per_location = self.browse(moves_ids).grouped('location_id')
            for location, mvs in moves_per_location.items():
                forecast_info = mvs._get_forecast_availability_outgoing(warehouse, location)
                for move in mvs:
                    move.forecast_availability, move.forecast_expected_date = forecast_info[move]