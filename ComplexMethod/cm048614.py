def create(self, vals_list):
        # OVERRIDE
        write_off_line_vals_list = []
        force_balance_vals_list = []
        linecomplete_line_vals_list = []

        for vals in vals_list:

            # Hack to add a custom write-off line.
            write_off_line_vals_list.append(vals.pop('write_off_line_vals', None))

            # Hack to force a custom balance.
            force_balance_vals_list.append(vals.pop('force_balance', None))

            # Hack to add a custom line.
            linecomplete_line_vals_list.append(vals.pop('line_ids', None))

        payments = super().create(vals_list)

        # Outstanding account should be set on the payment in community edition to force the generation of journal entries on the payment
        # This is required because no reconciliation is possible in community, which would prevent the user to reconcile the bank statement with the invoice
        accounting_installed = self.env['account.move']._get_invoice_in_payment_state() == 'in_payment'

        for i, (pay, vals) in enumerate(zip(payments, vals_list)):
            if (not accounting_installed and not pay.outstanding_account_id) or self.env.context.get('force_payment_move'):
                outstanding_account = pay._get_outstanding_account(pay.payment_type)
                pay.outstanding_account_id = outstanding_account.id

            if (
                write_off_line_vals_list[i] is not None
                or force_balance_vals_list[i] is not None
                or linecomplete_line_vals_list[i] is not None
            ):
                pay._generate_journal_entry(
                    write_off_line_vals=write_off_line_vals_list[i],
                    force_balance=force_balance_vals_list[i],
                    line_ids=linecomplete_line_vals_list[i],
                )
                # propagate the related fields to the move as it is being created after the payment
                if move_vals := {
                    fname: value
                    for fname, value in vals.items()
                    if self._fields[fname].related and (self._fields[fname].related or '').split('.')[0] == 'move_id'
                }:
                    pay.move_id.write(move_vals)
        return payments