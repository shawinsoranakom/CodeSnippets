def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()

        # liquidity_lines, counterpart_lines, writeoff_lines
        lines = [self.env['account.move.line'] for _dummy in range(3)]
        valid_account_types = self._get_valid_payment_account_types()
        for line in self.move_id.line_ids:
            if line.account_id in self._get_valid_liquidity_accounts():
                lines[0] += line  # liquidity_lines
            elif line.account_id.account_type in valid_account_types or line.account_id == line.company_id.transfer_account_id:
                lines[1] += line  # counterpart_lines
            else:
                lines[2] += line  # writeoff_lines

        # In some case, there is no liquidity or counterpart line (after changing an outstanding account on the journal for example)
        # In that case, and if there is one writeoff line, we take this line and set it as liquidity/counterpart line
        if len(lines[2]) == 1:
            for i in (0, 1):
                if not lines[i]:
                    lines[i] = lines[2]
                    lines[2] -= lines[2]

        return lines