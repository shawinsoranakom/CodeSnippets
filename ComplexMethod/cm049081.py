def search_remaining_qty(self, operator, value):
        if operator != '=' or not isinstance(value, bool) or value is not True:
            raise UserError(_("Only is set (= True) is supported in search for remaining_qty."))
        products = 'default_product_id' in self.env.context and self.env['product.product'].browse(self.env.context['default_product_id']) or self.env['product.product']
        if not products:
            products = self.env['product.product'].search([('is_storable', '=', True), ('qty_available', '>', 0)])
        move_ids = []
        for company in self.env.companies:
            for qty_by_move in products.with_company(company)._get_remaining_moves().values():
                for move in qty_by_move:
                    move_ids.append(move.id)
        return [('id', 'in', move_ids)]