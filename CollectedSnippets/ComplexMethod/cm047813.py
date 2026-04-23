def _are_finished_serials_already_produced(self, lots, excluded_sml=None):
        if not lots:
            return False
        excluded_sml = excluded_sml or self.env['stock.move.line']
        domain = [
            ('lot_id', 'in', lots.ids),
            ('quantity', '=', 1),
            ('state', '=', 'done')
        ]
        co_prod_move_lines = self.move_finished_ids.move_line_ids - excluded_sml
        domain_unbuild = domain + [
            ('production_id', '=', False),
            ('location_dest_id.usage', '=', 'production')
        ]
        # Check presence of same sn in previous productions
        duplicates = self.env['stock.move.line'].search_count(domain + [
            ('location_id.usage', '=', 'production'),
            ('move_id.unbuild_id', '=', False)
        ])
        if duplicates:
            # Maybe some move lines have been compensated by unbuild
            duplicates_unbuild = self.env['stock.move.line'].search_count(domain_unbuild + [
                ('move_id.unbuild_id', '!=', False)
            ])
            removed = self.env['stock.move.line'].search_count([
                ('lot_id', 'in', lots.ids),
                ('state', '=', 'done'),
                ('location_id.usage', '!=', 'inventory'),
                ('location_dest_id.usage', '=', 'inventory'),
            ])
            unremoved = self.env['stock.move.line'].search_count([
                ('lot_id', 'in', lots.ids),
                ('state', '=', 'done'),
                ('location_id.usage', '=', 'inventory'),
                ('location_dest_id.usage', '!=', 'inventory'),
            ])
            # Either removed or unbuild
            if not ((duplicates_unbuild or removed) and duplicates - duplicates_unbuild - removed + unremoved == 0):
                return True
        # Check presence of same sn in current production
        duplicates = co_prod_move_lines.filtered(lambda ml: ml.quantity and ml.lot_id.id in lots.ids)
        return bool(duplicates)