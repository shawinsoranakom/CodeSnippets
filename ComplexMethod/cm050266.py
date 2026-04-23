def _is_overlapping_period(self, date_from, date_to):
        """
        Return True if the employee is at least in contract one day during the period given
        :param date date_from: the start of the period
        :param date date_to: the stop of the period
        """
        if not (self.contract_date_start and date_from and date_to):
            return False
        period_start = date_from or date.min
        period_end = date_to or date.max
        contract_end = self.date_end or date.max
        return period_start <= contract_end and self.date_start <= period_end