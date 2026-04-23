def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        """ Returns the values to create the purchase order line from the current SO line.
            :param purchase_order: record of purchase.order
            :rtype: dict
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        self.ensure_one()
        # compute quantity from SO line UoM
        product_quantity = self.product_uom_qty
        if quantity:
            product_quantity = quantity

        purchase_qty_uom = self.product_uom_id._compute_quantity(product_quantity, self.product_id.uom_id)

        # determine vendor (real supplier, sharing the same partner as the one from the PO, but with more accurate informations like validity, quantity, ...)
        # Note: one partner can have multiple supplier info for the same product
        supplierinfo = self.product_id._select_seller(
            partner_id=purchase_order.partner_id,
            quantity=purchase_qty_uom,
            date=purchase_order.date_order and purchase_order.date_order.date(),  # and purchase_order.date_order[:10],
            uom_id=self.product_id.uom_id
        )
        if supplierinfo and supplierinfo.product_uom_id != self.product_id.uom_id:
            purchase_qty_uom = self.product_id.uom_id._compute_quantity(purchase_qty_uom, supplierinfo.product_uom_id)

        price_unit, taxes = self._purchase_service_get_price_unit_and_taxes(supplierinfo, purchase_order)
        name = self._purchase_service_get_product_name(supplierinfo, purchase_order, quantity)

        line_description = self.with_context(lang=self.order_id.partner_id.lang)._get_sale_order_line_multiline_description_variants()
        if line_description:
            name += line_description

        purchase_line_vals = {
            'name': name,
            'product_qty': purchase_qty_uom,
            'product_id': self.product_id.id,
            'product_uom_id': supplierinfo.product_uom_id.id or self.product_id.uom_id.id,
            'price_unit': price_unit,
            'date_planned': purchase_order.date_order + relativedelta(days=int(supplierinfo.delay)),
            'tax_ids': [(6, 0, taxes.ids)],
            'order_id': purchase_order.id,
            'sale_line_id': self.id,
            'discount': supplierinfo.discount,
        }
        if self.analytic_distribution:
            purchase_line_vals['analytic_distribution'] = self.analytic_distribution
        return purchase_line_vals