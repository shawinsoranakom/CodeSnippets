def _compute_invoice_status(self):
        def check_moves_state(moves):
            # All moves states are either 'done' or 'cancel', and there is at least one 'done'
            at_least_one_done = False
            for move in moves:
                if move.state not in ['done', 'cancel']:
                    return False
                at_least_one_done = at_least_one_done or move.state == 'done'
            return at_least_one_done
        super()._compute_invoice_status()
        for line in self:
            # We handle the following specific situation: a physical product is partially delivered,
            # but we would like to set its invoice status to 'Fully Invoiced'. The use case is for
            # products sold by weight, where the delivered quantity rarely matches exactly the
            # quantity ordered.
            if (
                line.state == 'sale'
                and line.invoice_status == 'no'
                and line.product_id.type in ['consu', 'product']
                and line.product_id.invoice_policy == 'delivery'
                and line.move_ids
                and check_moves_state(line.move_ids)
                and not float_is_zero(line.qty_delivered, precision_rounding=line.product_uom_id.rounding)
            ):
                line.invoice_status = 'invoiced'