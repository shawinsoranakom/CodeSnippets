def _get_alternative_values(self):
        vals = []
        origin_po = self.origin_po_id
        partner_product_tmpl_dict = {}
        if self.copy_products and origin_po:
            supplierinfo = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', 'in', origin_po.order_line.product_id.product_tmpl_id.ids),
                ('partner_id', 'in', self.partner_ids.ids),
                '|', ('product_code', '!=', False), ('product_name', '!=', False)
            ])
            # Build dict: {partner: set(product_tmpl_ids)}
            for info in supplierinfo:
                partner_product_tmpl_dict.setdefault(info.partner_id.id, set()).add(info.product_tmpl_id.id)

        for partner in self.partner_ids:
            product_tmpl_ids_with_description = partner_product_tmpl_dict.get(partner.id, set())
            val = {
                'date_order': origin_po.date_order,
                'partner_id': partner.id,
                'user_id': origin_po.user_id.id,
                'dest_address_id': origin_po.dest_address_id.id,
                'origin': origin_po.origin,
                'currency_id': partner.property_purchase_currency_id.id or self.env.company.currency_id.id,
                'payment_term_id': partner.property_supplier_payment_term_id.id,
            }
            if self.copy_products and origin_po:
                val['order_line'] = [Command.create(self._get_alternative_line_value(line, product_tmpl_ids_with_description)) for line in origin_po.order_line]
            vals.append(val)

        return vals