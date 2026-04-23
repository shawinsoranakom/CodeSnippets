def create(self, vals_list):
        if any('state' in vals and vals.get('state') == 'posted' for vals in vals_list):
            raise UserError(_('You cannot create a move already in the posted state. Please create a draft move and post it after.'))
        container = {'records': self}
        with self._check_balanced(container):
            with ExitStack() as exit_stack, self._sync_dynamic_lines(container):
                for vals in vals_list:
                    self._sanitize_vals(vals)
                stolen_moves = self.browse(set(move for vals in vals_list for move in self._stolen_move(vals)))
                moves = super().create(vals_list)
                exit_stack.enter_context(self.env.protecting([protected for vals, move in zip(vals_list, moves) for protected in self._get_protected_vals(vals, move)]))
                container['records'] = moves | stolen_moves
            for move, vals in zip(moves, vals_list):
                if 'tax_totals' in vals:
                    move.tax_totals = vals['tax_totals']
            moves.is_manually_modified = False
        return moves