def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        for re in res:
            if self.sale_line_id and re.get('location_final_id'):
                final_loc = self.env['stock.location'].browse(re.get('location_final_id'))
                if final_loc.usage == 'customer' or final_loc.usage == 'transit':
                    re['sale_line_id'] = self.sale_line_id.id
            if self.sale_line_id.route_ids:
                re['route_ids'] = [Command.link(route_id) for route_id in self.sale_line_id.route_ids.ids]
        return res