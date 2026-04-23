def _get_next_date(self, last_call):
        """
        Returns the next date with the given last call
        """
        self.ensure_one()
        if self.frequency in self._get_hourly_frequencies() + ['daily']:
            return last_call + relativedelta(days=1)

        if self.frequency == 'weekly':
            return last_call + relativedelta(days=1, weekday=int(self.week_day))

        if self.frequency == 'bimonthly':
            first_date = last_call + relativedelta(day=int(self.first_day))
            second_date = last_call + relativedelta(day=int(self.second_day))
            if last_call < first_date:
                return first_date
            if last_call < second_date:
                return second_date
            return last_call + relativedelta(day=int(self.first_day), months=1)

        if self.frequency == 'monthly':
            date = last_call + relativedelta(day=int(self.first_day))
            if last_call < date:
                return date
            return last_call + relativedelta(day=int(self.first_day), months=1)

        if self.frequency == 'biyearly':
            first_date = last_call + relativedelta(month=int(self.first_month), day=int(self.first_month_day))
            second_date = last_call + relativedelta(month=int(self.second_month), day=int(self.second_month_day))
            if last_call < first_date:
                return first_date
            if last_call < second_date:
                return second_date
            return last_call + relativedelta(month=int(self.first_month), day=int(self.first_month_day), years=1)

        if self.frequency == 'yearly':
            date = last_call + relativedelta(month=int(self.yearly_month), day=int(self.yearly_day))
            if last_call < date:
                return date
            return last_call + relativedelta(month=int(self.yearly_month), day=int(self.yearly_day), years=1)

        raise ValidationError(_("Your frequency selection is not correct: please choose a frequency between theses options:"
            "Hourly, Daily, Weekly, Twice a month, Monthly, Twice a year and Yearly."))