def _compute_name(self):
        # Take the description on the order template if the product is present in it
        super()._compute_name()
        for line in self:
            if line.product_id and line.order_id.sale_order_template_id and line._use_template_name():
                for template_line in line.order_id.sale_order_template_id.sale_order_template_line_ids:
                    if line.product_id == template_line.product_id and template_line.name:
                        # If a specific description was set on the template, use it
                        # Otherwise the description is handled by the super call
                        lang = line.order_id.partner_id.lang
                        line.name = template_line.with_context(lang=lang).name + line.with_context(lang=lang)._get_sale_order_line_multiline_description_variants()
                        break