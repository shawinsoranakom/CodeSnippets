def _update_order_line_info(
        self, product_id, quantity, *, section_id=False, child_field='order_line', **kwargs
    ):
        """ Update purchase order line information for a given product or create
        a new one if none exists yet.
        :param int product_id: The product, as a `product.product` id.
        :param int quantity: The quantity selected in the catalog.
        :param int section_id: The id of section selected in the catalog.
        :return: The unit price of the product, based on the pricelist of the
                 purchase order and the quantity selected.
        :rtype: float
        """
        self.ensure_one()
        pol = self.order_line.filtered(
            lambda l: l.product_id.id == product_id
            and l.get_parent_section_line().id == section_id
        )
        if pol:
            if quantity != 0:
                pol.product_qty = quantity
            elif self.state in ['draft', 'sent']:
                price_unit = self._get_product_price_and_data(pol.product_id)['price']
                pol.unlink()
                return price_unit
            else:
                pol.product_qty = 0
        elif quantity > 0:
            pol = self.env['purchase.order.line'].create({
                'order_id': self.id,
                'product_id': product_id,
                'product_qty': quantity,
                'sequence': self._get_new_line_sequence(child_field, section_id),
            })
            if pol.selected_seller_id:
                # Fix the PO line's price on the seller's one.
                seller = pol.selected_seller_id
                price = seller.price
                if seller.currency_id != self.currency_id:
                    price = seller.currency_id._convert(price, self.currency_id)
                pol.price_unit = pol.technical_price_unit = price
                pol.discount = seller.discount
        return pol.price_unit_discounted