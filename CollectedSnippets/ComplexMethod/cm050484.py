def _load_pos_data_search_read(self, data, config):
        limit_count = config.get_limited_product_count()
        pos_limited_loading = self.env.context.get('pos_limited_loading', True)
        if limit_count and pos_limited_loading:
            query = self._search(self._load_pos_data_domain(data, config), bypass_access=True)
            sql = SQL(
                """
                    WITH pm AS (
                        SELECT pp.product_tmpl_id,
                            MAX(sml.write_date) date
                        FROM stock_move_line sml
                        JOIN product_product pp ON sml.product_id = pp.id
                        GROUP BY pp.product_tmpl_id
                    )
                    SELECT product_template.id
                        FROM %s
                    LEFT JOIN pm ON product_template.id = pm.product_tmpl_id
                        WHERE %s
                    ORDER BY product_template.is_favorite DESC NULLS LAST,
                        CASE WHEN product_template.type = 'service' THEN 1 ELSE 0 END DESC,
                        pm.date DESC NULLS LAST,
                        product_template.write_date DESC
                    LIMIT %s
                """,
                query.from_clause,
                query.where_clause or SQL("TRUE"),
                limit_count,
            )
            product_tmpl_ids = [r[0] for r in self.env.execute_query(sql)]
            products = self._load_product_with_domain([('id', 'in', product_tmpl_ids)])
        else:
            domain = self._load_pos_data_domain(data, config)
            products = self._load_product_with_domain(domain)

        product_combo = products.filtered(lambda p: p['type'] == 'combo')
        products += product_combo.combo_ids.combo_item_ids.product_id.product_tmpl_id

        special_products = config._get_special_products().filtered(
                    lambda product: not product.sudo().company_id
                                    or product.sudo().company_id == self.env.company
                )
        products += special_products.product_tmpl_id
        if config.tip_product_id:
            tip_company_id = config.tip_product_id.sudo().company_id
            if not tip_company_id or tip_company_id == self.env.company:
                products += config.tip_product_id.product_tmpl_id

        # Ensure optional products are loaded when configured.
        if products.filtered(lambda p: p.pos_optional_product_ids):
            products |= products.mapped("pos_optional_product_ids")

        # Ensure products from loaded orders are loaded
        if data.get('pos.order.line'):
            products += self.env['product.product'].browse([l['product_id'] for l in data['pos.order.line']]).product_tmpl_id

        return self._load_pos_data_read(products, config)