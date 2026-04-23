def _compute_total_cost(self, stock_moves):
        """
        Compute the total cost of the order lines.
        :param stock_moves: recordset of `stock.move`, used for fifo/avco lines
        """
        for line in self.filtered(lambda l: not l.is_total_cost_computed):
            product = line.product_id
            cost_currency = product.sudo().cost_currency_id
            moves = line._get_stock_moves_to_consider(stock_moves, product) if stock_moves else None
            if moves and line._is_product_storable_fifo_avco():
                product_cost = line._get_product_cost_with_moves(moves)
                if cost_currency.is_zero(product_cost) and line.order_id.shipping_date:
                    if line.refunded_orderline_id:
                        product_cost = line.refunded_orderline_id.total_cost / line.refunded_orderline_id.qty
                    else:
                        product_cost = product.standard_price
            else:
                product_cost = product.standard_price
            line.total_cost = line.qty * cost_currency._convert(
                from_amount=product_cost,
                to_currency=line.currency_id,
                company=line.company_id or self.env.company,
                date=line.order_id.date_order or fields.Date.today(),
                round=False,
            )
            line.is_total_cost_computed = True