def _compute_price_unit_and_date_planned_and_name(self):
        po_lines_without_requisition = self.env['purchase.order.line']
        for pol in self:
            if pol.product_id.id not in pol.order_id.requisition_id.line_ids.product_id.ids:
                po_lines_without_requisition |= pol
                continue

            line = None
            # Match the requisition line with exact UoM first, then product-only as fallback.
            for req_line in pol.order_id.requisition_id.line_ids:
                if req_line.product_id == pol.product_id:
                    line = req_line
                    if req_line.product_uom_id == pol.product_uom_id:
                        break

            pol.price_unit = line.product_uom_id._compute_price(line.price_unit, pol.product_uom_id)
            partner = pol.order_id.partner_id or pol.order_id.requisition_id.vendor_id
            params = {'order_id': pol.order_id}
            seller = pol.product_id._select_seller(
                partner_id=partner,
                quantity=pol.product_qty,
                date=pol.order_id.date_order and pol.order_id.date_order.date(),
                uom_id=line.product_uom_id,
                params=params)
            if not pol.date_planned:
                pol.date_planned = pol._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            product_ctx = {'seller_id': seller.id, 'lang': get_lang(pol.env, partner.lang).code}
            name = pol._get_product_purchase_description(pol.product_id.with_context(product_ctx))
            if line.product_description_variants:
                name += '\n' + line.product_description_variants
            pol.name = name
        super(PurchaseOrderLine, po_lines_without_requisition)._compute_price_unit_and_date_planned_and_name()