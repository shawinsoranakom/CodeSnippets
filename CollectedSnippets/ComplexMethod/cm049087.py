def _prepare_analytic_lines(self):
        self.ensure_one()
        if not self._get_analytic_distribution() and not self.analytic_account_line_ids:
            return False

        if self.state in ['cancel', 'draft']:
            return False
        amount, unit_amount = 0, 0

        if self.state != 'done':
            if self.picked:
                unit_amount = self.product_uom._compute_quantity(
                    self.quantity, self.product_id.uom_id)
                # Falsy in FIFO but since it's an estimation we don't require exact correct cost. Otherwise
                # we would have to recompute all the analytic estimation at each out.
                amount = unit_amount * self.product_id.standard_price
            else:
                return False
        else:
            amount = self.value
            unit_amount = self._get_valued_qty()

        if self._is_out():
            amount = -amount

        if self.analytic_account_line_ids and amount == 0 and unit_amount == 0:
            self.analytic_account_line_ids.unlink()
            return False

        return self.env['account.analytic.account']._perform_analytic_distribution(
            self._get_analytic_distribution(), amount, unit_amount, self.analytic_account_line_ids, self)