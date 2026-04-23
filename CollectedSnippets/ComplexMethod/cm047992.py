def default_get(self, fields):
        res = super(AccountDebitNote, self).default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
        if any(move.state != "posted" for move in move_ids):
            raise UserError(_('You can only debit posted moves.'))
        elif any(move.debit_origin_id for move in move_ids):
            raise UserError(_("You can't make a debit note for an invoice that is already linked to a debit note."))
        elif any(move.move_type not in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'] for move in move_ids):
            raise UserError(_("You can make a debit note only for a Customer Invoice, a Customer Credit Note, a Vendor Bill or a Vendor Credit Note."))
        res['move_ids'] = [(6, 0, move_ids.ids)]
        return res