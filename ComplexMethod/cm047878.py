def _add_transit_line(self, move_raw, forecast, production, level, current_index):
        def is_related_to_production(document, production):
            if not document:
                return False
            return document.get('_name') == production._name and document.get('id') == production.id

        in_transit = next(filter(lambda line: line.get('in_transit') and is_related_to_production(line.get('document_out'), production), forecast), None)
        if not in_transit or is_related_to_production(in_transit.get('reservation'), production):
            return None

        product = move_raw.product_id
        currency = (production.company_id or self.env.company).currency_id
        lg = self.env['res.lang']._get_data(code=self.env.user.lang) or get_lang(self.env)
        receipt_date = datetime.strptime(in_transit['delivery_date'], lg.date_format)
        bom_missing_qty = max(0, production.product_uom_qty * move_raw.bom_line_id.product_qty - (move_raw.product_uom_qty - in_transit['quantity']))
        mo_cost = self._get_replenishment_mo_cost(product, in_transit['quantity'], in_transit['uom_id'], currency)
        bom_cost = self._get_replenishment_mo_cost(product, bom_missing_qty, in_transit['uom_id'], currency) if production.bom_id else False
        real_cost = product.standard_price * in_transit['uom_id']._compute_quantity(in_transit['quantity'], product.uom_id)
        if self._is_production_started(production) or not production.bom_id:
            mo_cost_decorator = self._get_comparison_decorator(real_cost, mo_cost, currency.rounding)
        else:
            mo_cost_decorator = self._get_comparison_decorator(bom_cost, mo_cost, currency.rounding)
        return {'summary': {
            'level': level + 1,
            'index': f"{current_index}IT",
            'name': _("In Transit"),
            'model': "in_transit",
            'product_model': product._name,
            'product_id': product.id,
            'quantity': min(move_raw.product_uom_qty, in_transit['uom_id']._compute_quantity(in_transit['quantity'], move_raw.product_uom)),  # Avoid over-rounding
            'uom_name': move_raw.product_uom.display_name,
            'uom_precision': self._get_uom_precision(move_raw.product_uom.rounding),
            'mo_cost': mo_cost,
            'mo_cost_decorator': mo_cost_decorator,
            'bom_cost': bom_cost,
            'real_cost': currency.round(real_cost),
            'receipt': self._check_planned_start(production.date_start, self._format_receipt_date('expected', receipt_date)),
            'currency_id': currency.id,
            'currency': currency,
        }}