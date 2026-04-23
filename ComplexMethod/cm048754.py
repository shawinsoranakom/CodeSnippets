def _reconcile_marked(self):
        """Process the pending reconciliation of entries marked (i.e. uring imports).

        The entries can be marked using the string `I*` as matching number where `*` can be anything.
        Once all the entries using identical numbers are posted, this function proceeds to do the real matching.
        """
        temp_numbers = list({
            line.matching_number
            for line in self
            if line.matching_number and line.matching_number.startswith('I')
        })
        if temp_numbers:
            for _matching_number, account, lines in self._read_group(
                domain=[('matching_number', 'in', temp_numbers)],
                groupby=['matching_number', 'account_id'],
                aggregates=['id:recordset'],
            ):
                if all(move.state == 'posted' for move in lines.move_id):
                    if not account.reconcile:
                        _logger.info("%s has reconciled lines, changing the config", account.display_name)
                        account.reconcile = True
                    lines.with_context(no_exchange_difference=True, no_cash_basis=True).reconcile()