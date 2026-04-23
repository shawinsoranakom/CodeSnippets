def _format_component_move(self, production, move_raw, replenishments, replenish_data, level, index):
        currency = (production.company_id or self.env.company).currency_id
        product = move_raw.product_id
        expected_quantity = move_raw.product_uom_qty
        current_quantity = move_raw.quantity
        replenish_mo_cost, _dummy_bom_cost, _dummy_real_cost = self._compute_cost_sums(replenishments)
        replenish_quantity = sum(rep.get('summary', {}).get('quantity', 0.0) for rep in replenishments)
        mo_quantity = current_quantity if production.state == 'done' else expected_quantity
        missing_quantity = mo_quantity - replenish_quantity
        missing_quantity_cost = self._get_component_real_cost(move_raw, missing_quantity)
        mo_cost = currency.round(replenish_mo_cost + missing_quantity_cost)
        real_cost = currency.round(self._get_component_real_cost(move_raw, current_quantity if move_raw.picked else 0))
        if production.bom_id:
            if move_raw.bom_line_id:
                qty_in_bom_uom = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id)
                bom_cost = currency.round(self._get_component_real_cost(move_raw, move_raw.bom_line_id.product_qty * qty_in_bom_uom / production.bom_id.product_qty))
            else:
                bom_cost = False
        else:
            bom_cost = currency.round(self._get_component_real_cost(move_raw, expected_quantity))
        cost_to_compare = real_cost if production.state != 'confirmed' else bom_cost
        if production.state == 'draft':
            mo_cost_decorator = self._get_comparison_decorator(bom_cost, mo_cost, currency.rounding)
        else:
            cost_to_compare = real_cost if production.state != 'confirmed' else bom_cost
            mo_cost_decorator = self._get_comparison_decorator(cost_to_compare, mo_cost, currency.rounding)
        component = {
            'level': level,
            'index': index,
            'id': product.id,
            'model': product._name,
            'name': product.display_name,
            'product_model': product._name,
            'product': product,
            'product_id': product.id,
            'quantity': expected_quantity if move_raw.state != 'done' else current_quantity,
            'uom': move_raw.product_uom,
            'uom_name': move_raw.product_uom.display_name,
            'uom_precision': self._get_uom_precision(move_raw.product_uom.rounding),
            'quantity_free': product.uom_id._compute_quantity(max(product.free_qty, 0), move_raw.product_uom) if product.is_storable else False,
            'quantity_on_hand': product.uom_id._compute_quantity(product.qty_available, move_raw.product_uom) if product.is_storable else False,
            'quantity_reserved': self._get_reserved_qty(move_raw, production.warehouse_id, replenish_data),
            'receipt': self._check_planned_start(production.date_start, self._get_component_receipt(product, move_raw, production.warehouse_id, replenishments, replenish_data)),
            'unit_cost': self._get_unit_cost(move_raw),
            'mo_cost': mo_cost,
            'mo_cost_decorator': 'danger' if isinstance(bom_cost, bool) and not bom_cost and not self._is_production_started(production) else mo_cost_decorator,
            'bom_cost': bom_cost,
            'real_cost': real_cost,
            'real_cost_decorator': False,
            'currency_id': currency.id,
            'currency': currency,
        }
        if not product.is_storable:
            return component
        if any(rep.get('summary', {}).get('model') == 'to_order' for rep in replenishments):
            # Means that there's an extra "To Order" line summing up what's left to order.
            component['formatted_state'] = _("To Order")
            component['state'] = 'to_order'

        return component