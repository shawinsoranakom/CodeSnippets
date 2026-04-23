def load_product_from_pos(self, config_id, domain, offset=0, limit=0):
        load_archived = self.env.context.get('load_archived', False)
        domain = Domain(domain)
        config = self.env['pos.config'].browse(config_id)
        product_tmpls = self._load_product_with_domain(domain, load_archived, offset, limit)

        # product.combo and product.combo.item loading
        for product_tmpl in product_tmpls:
            if product_tmpl.type == 'combo':
                product_tmpls += product_tmpl.combo_ids.combo_item_ids.product_id.product_tmpl_id

        combo_domain = Domain('id', 'in', product_tmpls.combo_ids.ids)
        combo_records = self.env['product.combo'].search(combo_domain)
        combo_read = self.env['product.combo']._load_pos_data_read(combo_records, config)
        combo_item_domain = Domain('combo_id', 'in', product_tmpls.combo_ids.ids)
        combo_item_records = self.env['product.combo.item'].search(combo_item_domain)
        combo_item_read = self.env['product.combo.item']._load_pos_data_read(combo_item_records, config)

        products = product_tmpls.product_variant_ids

        # product.pricelist_item & product.pricelist loading
        pricelists = config.current_session_id.get_pos_ui_product_pricelist_item_by_product(
            product_tmpls.ids,
            products.ids,
            config.id
        )

        # product.template.attribute.value & product.template.attribute.line loading
        product_tmpl_attr_line = product_tmpls.attribute_line_ids
        product_tmpl_attr_line_read = product_tmpl_attr_line._load_pos_data_read(product_tmpl_attr_line, config)
        product_tmpl_attr_value = product_tmpls.attribute_line_ids.product_template_value_ids
        product_tmpl_attr_value_read = product_tmpl_attr_value._load_pos_data_read(product_tmpl_attr_value, config)

        # product.template.attribute.exclusion loading
        product_tmpl_excl = self.env['product.template.attribute.exclusion']
        product_tmpl_exclusion = product_tmpl_attr_value.exclude_for + product_tmpl_excl.search([
            ('product_tmpl_id', 'in', product_tmpls.ids),
        ])
        product_tmpl_exclusion_read = product_tmpl_excl._load_pos_data_read(product_tmpl_exclusion, config)

        # product.product loading
        product_read = products._load_pos_data_read(products.with_context(display_default_code=False), config)

        # product.template loading
        product_tmpl_read = self._load_pos_data_read(product_tmpls, config)

        # product.uom loading
        packaging_domain = Domain('product_id', 'in', products.ids)
        barcode_in_domain = any('barcode' in condition.field_expr for condition in domain.iter_conditions())

        if barcode_in_domain:
            barcode = [condition.value for condition in domain.iter_conditions() if 'barcode' in condition.field_expr]
            flat = [item for sublist in barcode for item in sublist]
            packaging_domain |= Domain('barcode', 'in', flat)

        product_uom = self.env['product.uom']
        packaging = product_uom.search(packaging_domain)
        condition = packaging and packaging.product_id
        packaging_read = product_uom._load_pos_data_read(packaging, config) if condition else []

        # account.tax loading
        account_tax = self.env['account.tax']
        tax_domain = Domain(account_tax._check_company_domain(config.company_id.id))
        tax_domain &= Domain('id', 'in', product_tmpls.taxes_id.ids)
        tax_read = account_tax._load_pos_data_read(account_tax.search(tax_domain), config)

        return {
            **pricelists,
            'account.tax': tax_read,
            'product.product': product_read,
            'product.template': product_tmpl_read,
            'product.uom': packaging_read,
            'product.combo': combo_read,
            'product.combo.item': combo_item_read,
            'product.template.attribute.value': product_tmpl_attr_value_read,
            'product.template.attribute.line': product_tmpl_attr_line_read,
            'product.template.attribute.exclusion': product_tmpl_exclusion_read,
        }