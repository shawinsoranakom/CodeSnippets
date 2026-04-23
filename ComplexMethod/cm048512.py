def _get_communication(self, lines):
        ''' Helper to compute the communication based on lines.
        :param lines:           A recordset of the `account.move.line`'s that will be reconciled.
        :return:                A string representing a communication to be set on payment.
        '''
        if len(lines.move_id) == 1:
            move = lines.move_id
            label = move.payment_reference or move.ref or move.name
        elif any(move.is_outbound() for move in lines.move_id):
            # outgoing payments references should use moves references
            labels = {move.payment_reference or move.ref or move.name for move in lines.move_id}
            return ', '.join(sorted(filter(lambda l: l, labels)))
        else:
            label = self.company_id.get_next_batch_payment_communication()
        return label