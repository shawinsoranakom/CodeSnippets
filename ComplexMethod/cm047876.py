def _get_component_receipt(self, product, move, warehouse, replenishments, replenish_data):
        def get(replenishment, key, check_in_receipt=False):
            fetch = replenishment.get('summary', {})
            if check_in_receipt:
                fetch = fetch.get('receipt', {})
            return fetch.get(key, False)

        if any(get(rep, 'type', True) == 'unavailable' for rep in replenishments):
            return self._format_receipt_date('unavailable')
        if not product.is_storable or move.state == 'done':
            return self._format_receipt_date('available')

        has_to_order_line = any(rep.get('summary', {}).get('model') == 'to_order' for rep in replenishments)
        reserved_quantity = self._get_reserved_qty(move, warehouse, replenish_data)
        missing_quantity = move.product_uom_qty - reserved_quantity
        free_qty = product.uom_id._compute_quantity(product.free_qty, move.product_uom)
        if move.product_uom.compare(missing_quantity, 0.0) <= 0 \
           or (not has_to_order_line
               and move.product_uom.compare(missing_quantity, free_qty) <= 0):
            return self._format_receipt_date('available')

        replenishments_with_date = list(filter(lambda r: r.get('summary', {}).get('receipt', {}).get('date'), replenishments))
        max_date = max([get(rep, 'date', True) for rep in replenishments_with_date], default=fields.Datetime.today())
        if has_to_order_line or any(get(rep, 'type', True) == 'estimated' for rep in replenishments):
            return self._format_receipt_date('estimated', max_date)
        else:
            return self._format_receipt_date('expected', max_date)