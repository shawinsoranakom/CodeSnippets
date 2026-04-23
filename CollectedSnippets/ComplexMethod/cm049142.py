def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, partner_id, po):
        values = self.env.context.get('procurement_values', {})
        uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_id, rounding_method='HALF-UP')
        # _select_seller is used if the supplier have different price depending
        # the quantities ordered.
        today = fields.Date.today()
        seller = product_id.with_company(company_id)._select_seller(
            partner_id=partner_id,
            quantity=product_qty if values.get('force_uom') else uom_po_qty,
            date=po.date_order and max(po.date_order.date(), today) or today,
            uom_id=product_uom if values.get('force_uom') else product_id.uom_id,
            params={'force_uom': values.get('force_uom')}
        )
        if seller and (seller.product_uom_id or seller.product_tmpl_id.uom_id) != product_uom:
            uom_po_qty = product_id.uom_id._compute_quantity(uom_po_qty, seller.product_uom_id, rounding_method='HALF-UP')

        tax_domain = self.env['account.tax']._check_company_domain(company_id)
        product_taxes = product_id.supplier_taxes_id.filtered_domain(tax_domain)
        taxes = po.fiscal_position_id.map_tax(product_taxes)

        if seller:
            price_unit = (seller.product_uom_id._compute_price(seller.price, product_uom) if product_uom else seller.price)
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
            price_unit, product_taxes, taxes, company_id)
        else:
            price_unit = 0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())

        product_lang = product_id.with_prefetch().with_context(
            lang=partner_id.lang,
            partner_id=partner_id.id,
        )
        name = product_lang.with_context(seller_id=seller.id).display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = self.order_id.date_planned or self._get_date_planned(seller, po=po)
        discount = seller.discount or 0.0

        return {
            'name': name,
            'product_qty': product_qty if product_uom else uom_po_qty,
            'product_id': product_id.id,
            'product_uom_id': product_uom.id or seller.product_uom_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'tax_ids': [(6, 0, taxes.ids)],
            'order_id': po.id,
            'discount': discount,
        }