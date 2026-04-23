def _compute_status_in_payment(self):
        for move in self:
            if move.state == 'posted':
                if move.payment_state in ('partial', 'in_payment', 'paid', 'reversed'):
                    move.status_in_payment = move.payment_state
                elif move.is_move_sent:
                    move.status_in_payment = 'sent'
            elif move.state == 'draft':
                if move.payment_state in ('partial', 'in_payment', 'paid'):
                    move.status_in_payment = move.payment_state

            if not move.status_in_payment:
                move.status_in_payment = move.state