def _compute_partner_ref(self):
        for product in self:
            for supplier_info in product.seller_ids:
                if supplier_info.partner_id.id == product.env.context.get('partner_id'):
                    product_name = supplier_info.product_name or product.default_code or product.name
                    product.partner_ref = '%s%s' % (product.code and '[%s] ' % product.code or '', product_name)
                    break
            else:
                product.partner_ref = product.display_name