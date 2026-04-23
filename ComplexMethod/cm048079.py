def _get_previous_date(self, last_call):
        """
        Returns the date a potential previous call would have been at
        For example if you have a monthly level giving 16/02 would return 01/02
        Contrary to `_get_next_date` this function will return the 01/02 if that date is given
        """
        self.ensure_one()
        if self.frequency in self._get_hourly_frequencies() + ['daily']:
            return last_call

        if self.frequency == 'weekly':
            return last_call + relativedelta(days=-6, weekday=int(self.week_day))

        if self.frequency == 'bimonthly':
            first_date = last_call + relativedelta(day=int(self.first_day))
            second_date = last_call + relativedelta(day=int(self.second_day))
            if last_call >= second_date:
                return second_date
            if last_call >= first_date:
                return first_date
            return last_call + relativedelta(day=int(self.second_day), months=-1)

        if self.frequency == 'monthly':
            date = last_call + relativedelta(day=int(self.first_day))
            if last_call >= date:
                return date
            return last_call + relativedelta(day=int(self.first_day), months=-1, days=1)

        if self.frequency == 'biyearly':
            first_date = last_call + relativedelta(month=int(self.first_month), day=int(self.first_month_day))
            second_date = last_call + relativedelta(month=int(self.second_month), day=int(self.second_month_day))
            if last_call >= second_date:
                return second_date
            if last_call >= first_date:
                return first_date
            return last_call + relativedelta(month=int(self.second_month), day=int(self.second_month_day), years=-1)

        if self.frequency == 'yearly':
            year_date = last_call + relativedelta(month=int(self.yearly_month), day=int(self.yearly_day))
            if last_call >= year_date:
                return year_date
            return last_call + relativedelta(month=int(self.yearly_month), day=int(self.yearly_day), years=-1)

        raise ValidationError(_("Your frequency selection is not correct: please choose a frequency between theses options:"
            "Hourly, Daily, Weekly, Twice a month, Monthly, Twice a year and Yearly."))