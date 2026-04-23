def _sale_get_invoice_price(self, order):
        """ Based on the current stock move, compute the price to reinvoice the analytic line that is going to be created (so the
            price of the sale line).
        """
        self.ensure_one()

        if self.product_id.expense_policy == 'sales_price':
            return order.pricelist_id._get_product_price(
                self.product_id,
                1.0,
                uom=self.product_uom,
                date=order.date_order,
            )

        uom_precision_digits = self.env['decimal.precision'].precision_get('Product Unit')
        if float_is_zero(self.quantity, precision_digits=uom_precision_digits):
            return 0.0

        price_unit = self.product_id.standard_price
        # Prevent unnecessary currency conversion that could be impacted by exchange rate
        # fluctuations
        if self.company_id.currency_id and price_unit and self.company_id.currency_id == order.currency_id:
            return self.company_id.currency_id.round(price_unit)

        currency_id = self.company_id.currency_id
        if currency_id and currency_id != order.currency_id:
            price_unit = currency_id._convert(price_unit, order.currency_id, order.company_id, order.date_order or fields.Date.today())
        return price_unit