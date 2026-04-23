def _compute_date(self):
        for move in self:
            accounting_date = move._get_accounting_date_source()
            if not accounting_date or not move.is_invoice(include_receipts=True):
                if not move.date:
                    move.date = fields.Date.context_today(self)
                continue
            if not move.is_sale_document(include_receipts=True):
                accounting_date = move._get_accounting_date(accounting_date, move._affect_tax_report())
            if accounting_date and accounting_date != move.date:
                move.date = accounting_date
                # _affect_tax_report may trigger premature recompute of line_ids.date
                self.env.add_to_compute(move.line_ids._fields['date'], move.line_ids)
                # might be protected because `_get_accounting_date` requires the `name`
                self.env.add_to_compute(self._fields['name'], move)