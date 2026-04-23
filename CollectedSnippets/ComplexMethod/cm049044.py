def _compute_display_name(self):
        name_per_id = self._additional_name_per_id()
        for so_line in self.sudo():
            if so_line.order_partner_id.lang:
                so_line = so_line.with_context(lang=so_line.order_id._get_lang())
            if (product := so_line.product_id).display_name:
                default_name = so_line._get_sale_order_line_multiline_description_sale()
                if so_line.name == default_name:
                    description = product.display_name
                else:
                    parts = (so_line.name or "").split('\n', 2)
                    description = parts[1] if len(parts) > 1 and parts[1] else product.display_name
            else:
                description = (so_line.name or "").split('\n', 1)[0]
            name = f"{so_line.order_id.name} - {description}"
            additional_name = name_per_id.get(so_line.id)
            if additional_name:
                name = f'{name} {additional_name}'
            so_line.display_name = name