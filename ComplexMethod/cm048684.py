def _get_accounting_date(self, invoice_date, has_tax, lock_dates=None):
        """Get correct accounting date for previous periods, taking tax lock date and affected journal into account.
        When registering an invoice in the past, we still want the sequence to be increasing.
        We then take the last day of the period, depending on the sequence format.

        If there is a tax lock date and there are taxes involved, we register the invoice at the
        last date of the first open period.
        :param invoice_date (datetime.date): The invoice date
        :param has_tax (bool): Iff any taxes are involved in the lines of the invoice
        :param lock_dates: Like result from `_get_violated_lock_dates`;
                           Can be used to avoid recomputing them in case they are already known.
        :rtype: datetime.date
        """
        self.ensure_one()
        lock_dates = lock_dates or self._get_violated_lock_dates(invoice_date, has_tax)
        today = fields.Date.context_today(self)
        highest_name = self.highest_name or self._get_last_sequence(relaxed=True)
        number_reset = self._deduce_sequence_number_reset(highest_name)
        if lock_dates:
            invoice_date = lock_dates[-1][0] + timedelta(days=1)
        if self.is_sale_document(include_receipts=True):
            if lock_dates:
                if not highest_name or number_reset == 'month':
                    return min(today, date_utils.get_month(invoice_date)[1])
                elif number_reset == 'year':
                    return min(today, date_utils.end_of(invoice_date, 'year'))
        else:
            if not highest_name or number_reset in ('month', 'year_range_month'):
                if (today.year, today.month) > (invoice_date.year, invoice_date.month):
                    return date_utils.get_month(invoice_date)[1]
                else:
                    return max(invoice_date, today)
            elif number_reset == 'year':
                if today.year > invoice_date.year:
                    return date(invoice_date.year, 12, 31)
                else:
                    return max(invoice_date, today)
        return invoice_date