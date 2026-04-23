def _get_replenishment_lines(self, production, move_raw, replenish_data, level, current_index):
        product = move_raw.product_id
        quantity = move_raw.product_uom_qty if move_raw.state != 'done' else move_raw.quantity
        reserved_quantity = self._get_reserved_qty(move_raw, production.warehouse_id, replenish_data)
        currency = (production.company_id or self.env.company).currency_id
        forecast = replenish_data['products'][product.id].get('forecast', [])
        current_lines = filter(lambda line: line.get('document_in', False) and line.get('document_out', False)
                               and line['document_out'].get('id', False) == production.id and not line.get('already_used'), forecast)
        total_ordered = 0
        replenishments = []
        for count, forecast_line in enumerate(current_lines):
            if move_raw.product_uom.compare(total_ordered, quantity - reserved_quantity) >= 0:
                # If a same product is used twice in the same MO, don't duplicate the replenishment lines
                break
            doc_in = self.env[forecast_line['document_in']['_name']].browse(forecast_line['document_in']['id'])
            replenishment_index = f"{current_index}{count}"
            replenishment = {}
            forecast_uom_id = forecast_line['uom_id']
            line_quantity = min(quantity, forecast_uom_id._compute_quantity(forecast_line['quantity'], move_raw.product_uom))  # Avoid over-rounding
            bom_quantity = production.product_uom_qty * move_raw.bom_line_id.product_qty - (quantity - line_quantity)
            replenishment['summary'] = {
                'level': level + 1,
                'index': replenishment_index,
                'id': doc_in.id,
                'model': doc_in._name,
                'name': doc_in.display_name,
                'product_model': product._name,
                'product_id': product.id,
                'state': doc_in.state,
                'quantity': line_quantity,
                'uom_name': move_raw.product_uom.display_name,
                'uom_precision': self._get_uom_precision(forecast_line['uom_id']['rounding']),
                'unit_cost': self._get_unit_cost(move_raw),
                'mo_cost': forecast_line.get('cost', self._get_replenishment_mo_cost(product, line_quantity, move_raw.product_uom, currency, forecast_line.get('move_in'))),
                'bom_cost': currency.round(self._get_component_real_cost(move_raw, bom_quantity)) if bom_quantity else False,
                'real_cost': currency.round(self._get_component_real_cost(move_raw, line_quantity)),
                'currency_id': currency.id,
                'currency': currency,
            }
            forecast_line['already_used'] = True
            if doc_in._name == 'mrp.production':
                replenishment['components'] = self._get_components_data(doc_in, replenish_data, level + 2, replenishment_index)
                replenishment['operations'] = self._get_operations_data(doc_in, level + 2, replenishment_index)
                initial_mo_cost, initial_bom_cost, initial_real_cost = self._compute_cost_sums(replenishment['components'], replenishment['operations'])
                remaining_cost_share, byproducts = self._get_byproducts_data(doc_in, initial_mo_cost, initial_bom_cost, initial_real_cost, level + 2, replenishment_index)
                replenishment['byproducts'] = byproducts
                replenishment['summary']['mo_cost'] = initial_mo_cost * remaining_cost_share
                replenishment['summary']['bom_cost'] = initial_bom_cost * remaining_cost_share
                replenishment['summary']['real_cost'] = initial_real_cost * remaining_cost_share

            if self._is_doc_in_done(doc_in):
                replenishment['summary']['receipt'] = self._format_receipt_date('available')
            else:
                replenishment['summary']['receipt'] = self._check_planned_start(production.date_start, self._get_replenishment_receipt(doc_in, replenishment.get('components', [])))

            if self._is_production_started(production):
                replenishment['summary']['mo_cost_decorator'] = self._get_comparison_decorator(replenishment['summary']['real_cost'], replenishment['summary']['mo_cost'], replenishment['summary']['currency'].rounding)
            else:
                replenishment['summary']['mo_cost_decorator'] = self._get_comparison_decorator(replenishment['summary']['bom_cost'], replenishment['summary']['mo_cost'], replenishment['summary']['currency'].rounding)
            replenishment['summary']['formatted_state'] = self._format_state(doc_in, replenishment['components']) if doc_in._name == 'mrp.production' else self._format_state(doc_in)
            replenishments.append(replenishment)
            total_ordered += replenishment['summary']['quantity']

        # Add "In transit" line if necessary
        in_transit_line = self._add_transit_line(move_raw, forecast, production, level, current_index)
        if in_transit_line:
            total_ordered += in_transit_line['summary']['quantity']
            replenishments.append(in_transit_line)

        # Avoid creating a "to_order" line to compensate for missing stock (i.e. negative free_qty).
        free_qty = max(0, product.uom_id._compute_quantity(product.free_qty, move_raw.product_uom))
        available_qty = reserved_quantity + free_qty + total_ordered
        missing_quantity = quantity - available_qty
        qty_in_bom_uom = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id)
        bom_missing_quantity = qty_in_bom_uom * move_raw.bom_line_id.product_qty - (reserved_quantity + free_qty + total_ordered)

        if product.is_storable and production.state not in ('done', 'cancel')\
           and move_raw.product_uom.compare(missing_quantity, 0) > 0:
            # Need to order more products to fulfill the need
            resupply_rules = self._get_resupply_rules(production, product, replenish_data)
            rules_delay = sum(rule.delay for rule in resupply_rules)
            resupply_data = self._get_resupply_data(resupply_rules, rules_delay, missing_quantity, move_raw.product_uom, product, production)

            to_order_line = {'summary': {
                'level': level + 1,
                'index': f"{current_index}TO",
                'name': _("To Order"),
                'model': "to_order",
                'product_model': product._name,
                'product_id': product.id,
                'quantity': missing_quantity,
                'replenish_quantity': move_raw.product_uom._compute_quantity(missing_quantity, product.uom_id),
                'uom_name': move_raw.product_uom.display_name,
                'uom_precision': self._get_uom_precision(move_raw.product_uom.rounding),
                'real_cost': currency.round(product.standard_price * move_raw.product_uom._compute_quantity(available_qty, product.uom_id)),
                'currency_id': currency.id,
                'currency': currency,
            }}
            if resupply_data:
                mo_cost = resupply_data['currency']._convert(resupply_data['cost'], currency, (production.company_id or self.env.company), fields.Date.today())
                to_order_line['summary']['mo_cost'] = mo_cost
                to_order_line['summary']['bom_cost'] = currency.round(self._get_component_real_cost(move_raw, bom_missing_quantity))
                to_order_line['summary']['receipt'] = self._check_planned_start(production.date_start, self._format_receipt_date('estimated', fields.Datetime.today() + timedelta(days=resupply_data['delay'])))
            else:
                to_order_line['summary']['mo_cost'] = currency.round(product.standard_price * move_raw.product_uom._compute_quantity(missing_quantity, product.uom_id))
                to_order_line['summary']['bom_cost'] = currency.round(self._get_component_real_cost(move_raw, bom_missing_quantity))
                to_order_line['summary']['receipt'] = self._format_receipt_date('unavailable')
            to_order_line['summary']['unit_cost'] = currency.round(to_order_line['summary']['mo_cost'] / missing_quantity)

            if self._is_production_started(production):
                to_order_line['summary']['mo_cost_decorator'] = self._get_comparison_decorator(to_order_line['summary']['real_cost'], to_order_line['summary']['mo_cost'], currency.rounding)
            else:
                to_order_line['summary']['mo_cost_decorator'] = self._get_comparison_decorator(to_order_line['summary']['bom_cost'], to_order_line['summary']['mo_cost'], currency.rounding)

            replenishments.append(to_order_line)

        return replenishments