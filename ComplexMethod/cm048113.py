def _verify_updated_quantity(self, order_line, product_id, new_qty, uom_id, **kwargs):
        self.ensure_one()
        product = self.env['product.product'].browse(product_id)
        if product.is_storable and not product.allow_out_of_stock_order:
            uom = self.env['uom.uom'].browse(uom_id)
            product_uom = product.uom_id

            product_qty_in_cart, available_qty = self._get_cart_and_free_qty(product)

            # Convert cart and available quantities to the requested uom
            product_qty_in_cart = product_uom._compute_quantity(product_qty_in_cart, uom)
            available_qty = product_uom._compute_quantity(available_qty, uom, round=False)
            available_qty = float_round(available_qty, precision_digits=0, rounding_method='DOWN')

            old_qty = order_line.product_uom_qty if order_line else 0
            added_qty = new_qty - old_qty
            total_cart_qty = product_qty_in_cart + added_qty
            if available_qty < total_cart_qty:
                allowed_line_qty = available_qty - (product_qty_in_cart - old_qty)
                if allowed_line_qty > 0:
                    def format_qty(qty):
                        return int(qty) if float(qty).is_integer() else qty
                    if order_line:
                        warning = order_line._set_shop_warning_stock(
                            format_qty(total_cart_qty),
                            format_qty(available_qty),
                            save=False,
                        )
                    else:
                        warning = self.env._(
                            "You ask for %(desired_qty)s products but only %(available_qty)s is"
                            " available.",
                            desired_qty=format_qty(total_cart_qty),
                            available_qty=format_qty(available_qty),
                        )
                elif order_line:
                    # Line will be deleted
                    warning = self.env._(
                        "Some products became unavailable and your cart has been updated. We're"
                        " sorry for the inconvenience."
                    )
                else:
                    warning = self.env._(
                        "%(product_name)s has not been added to your cart since it is not available.",
                        product_name=product.name,
                    )
                return allowed_line_qty, warning
        return super()._verify_updated_quantity(order_line, product_id, new_qty, uom_id, **kwargs)