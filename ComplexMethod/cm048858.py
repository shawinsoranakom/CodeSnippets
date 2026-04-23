def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        partner = values['supplier'].partner_id
        procurement_uom_po_qty = product_uom._compute_quantity(product_qty, line.product_uom_id, rounding_method='HALF-UP')
        seller = product_id.with_company(company_id)._select_seller(
            partner_id=partner,
            quantity=line.product_qty + procurement_uom_po_qty,
            date=line.order_id.date_order and line.order_id.date_order.date(),
            uom_id=line.product_uom_id,
            params={'force_uom': values.get('force_uom')})

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.sudo().tax_ids, company_id) if seller else 0.0
        if price_unit and seller and line.order_id.currency_id and seller.currency_id != line.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, line.order_id.currency_id, line.order_id.company_id, fields.Date.today())

        res = {
            'product_qty': line.product_qty + procurement_uom_po_qty,
            'price_unit': price_unit,
            'move_dest_ids': [(4, x.id) for x in values.get('move_dest_ids', [])]
        }
        if seller.product_uom_id != line.product_uom_id and not values.get('force_uom'):
            res['product_qty'] = line.product_uom_id._compute_quantity(res['product_qty'], seller.product_uom_id, rounding_method='HALF-UP')
            res['product_uom_id'] = seller.product_uom_id
        orderpoint_id = values.get('orderpoint_id')
        if orderpoint_id:
            res['orderpoint_id'] = orderpoint_id.id
        return res