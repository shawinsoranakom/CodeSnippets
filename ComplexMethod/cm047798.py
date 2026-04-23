def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for production, vals in zip(self, vals_list):
            # covers at least 2 cases: backorders generation (follow default logic for moves copying)
            # and copying a done MO via the form (i.e. copy only the non-cancelled moves since no backorder = cancelled finished moves)
            if not default or 'move_finished_ids' not in default:
                move_finished_ids = production.move_finished_ids
                if production.state != 'cancel':
                    move_finished_ids = production.move_finished_ids.filtered(lambda m: m.state != 'cancel' and m.product_qty != 0.0)
                vals['move_finished_ids'] = [(0, 0, move_vals) for move_vals in move_finished_ids.copy_data()]
            if not default or 'move_raw_ids' not in default:
                vals['move_raw_ids'] = [(0, 0, move_vals) for move_vals in production.move_raw_ids.filtered(lambda m: m.product_qty != 0.0).copy_data()]
        return vals_list