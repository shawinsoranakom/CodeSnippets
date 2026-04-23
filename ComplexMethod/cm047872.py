def _get_mo_summary(self, production, components, operations, current_mo_cost, current_bom_cost, current_real_cost, remaining_cost_share):
        currency = (production.company_id or self.env.company).currency_id
        product = production.product_id
        mo_cost = current_mo_cost * remaining_cost_share
        bom_cost = current_bom_cost * remaining_cost_share
        real_cost = current_real_cost * remaining_cost_share
        decorator = self._get_comparison_decorator(real_cost if self._is_production_started(production) else bom_cost, mo_cost, currency.rounding)
        mo_cost_decorator = decorator if any(compo['summary']['mo_cost_decorator'] == decorator for compo in (components + [operations])) else False
        real_cost_temp_decorator = self._get_comparison_decorator(mo_cost, real_cost, currency.rounding) if self._is_production_started(production) else False
        real_cost_decorator = real_cost_temp_decorator if any(compo['summary']['real_cost_decorator'] == real_cost_temp_decorator for compo in (components + [operations])) else False
        return {
            'level': 0,
            'model': production._name,
            'id': production.id,
            'name': production.product_id.display_name,
            'product_model': production.product_id._name,
            'product_id': production.product_id.id,
            'state': production.state,
            'formatted_state': self._format_state(production, components),
            'has_bom': bool(production.bom_id),
            'quantity': production.product_qty if production.state != 'done' else production.qty_produced,
            'uom_name': production.product_uom_id.display_name,
            'uom_precision': self._get_uom_precision(production.product_uom_id.rounding or 0.01),
            'quantity_free': product.uom_id._compute_quantity(max(product.free_qty, 0), production.product_uom_id) if product.is_storable else False,
            'quantity_on_hand': product.uom_id._compute_quantity(product.qty_available, production.product_uom_id) if product.is_storable else False,
            'quantity_reserved': 0.0,
            'receipt': self._check_planned_start(production.date_deadline, self._get_replenishment_receipt(production, components)),
            'unit_cost': self._get_unit_cost(production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id)),
            'mo_cost': currency.round(mo_cost),
            'mo_cost_decorator': mo_cost_decorator,
            'real_cost_decorator': real_cost_decorator if not mo_cost_decorator else False,
            'bom_cost': currency.round(bom_cost),
            'real_cost': currency.round(real_cost),
            'currency_id': currency.id,
            'currency': currency,
        }