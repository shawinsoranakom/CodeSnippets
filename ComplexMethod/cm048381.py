def _check_multiwarehouse_group(self):
        cnt_by_company = self.env['stock.warehouse'].sudo()._read_group([('active', '=', True)], ['company_id'], aggregates=['__count'])
        if cnt_by_company:
            max_count = max(count for company, count in cnt_by_company)
            group_user = self.env.ref('base.group_user')
            group_stock_multi_warehouses = self.env.ref('stock.group_stock_multi_warehouses')
            group_stock_multi_locations = self.env.ref('stock.group_stock_multi_locations')
            if max_count <= 1 and group_stock_multi_warehouses in group_user.implied_ids:
                group_user.write({'implied_ids': [(3, group_stock_multi_warehouses.id)]})
                group_stock_multi_warehouses.write({'user_ids': [(3, user.id) for user in group_user.all_user_ids]})
            if max_count > 1 and group_stock_multi_warehouses not in group_user.implied_ids:
                if group_stock_multi_locations not in group_user.implied_ids:
                    self.env['res.config.settings'].create({
                        'group_stock_multi_locations': True,
                    }).execute()
                group_user.write({'implied_ids': [(4, group_stock_multi_warehouses.id), (4, group_stock_multi_locations.id)]})