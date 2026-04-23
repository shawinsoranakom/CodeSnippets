def _get_period_of_time(self):
        self.ensure_one()
        today = fields.Datetime.now()
        start_date = limit_date = today
        if self.based_on == 'one_week':
            start_date = start_date - relativedelta(weeks=1)
        elif self.based_on == 'one_month':
            start_date = start_date - relativedelta(months=1)
        elif self.based_on == 'three_months':
            start_date = start_date - relativedelta(months=3)
        elif self.based_on == 'one_year':
            start_date = start_date - relativedelta(years=1)
        else:  # Relative period of time.
            start_date = datetime(year=today.year - 1, month=today.month, day=1)
            if self.based_on == 'last_year_2':
                start_date += relativedelta(months=1)
            elif self.based_on == 'last_year_3':
                start_date += relativedelta(months=2)
            if self.based_on == 'last_year_quarter':
                limit_date = start_date + relativedelta(months=3)
            else:
                limit_date = start_date + relativedelta(months=1)
        return start_date, limit_date