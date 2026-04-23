def _l10n_in_is_full_day_request(self, hours=None, default_hours=None):
        self.ensure_one()
        default_hours = default_hours or self._l10n_in_get_default_leave_hours()
        hours = hours if hours is not None else (self.number_of_hours or 0.0)
        if self.leave_type_request_unit == 'hour':
            return bool(default_hours) and float_compare(hours, default_hours, precision_digits=2) >= 0
        if (
            self.request_date_from_period != self.request_date_to_period
            and (self.request_date_from_period != "pm" or self.request_date_to_period != "am")
        ) or not default_hours:
            return True
        return float_compare(hours, default_hours, precision_digits=2) >= 0