def _get_durations(self, check_leave_type=True, resource_calendar=None):
        result = super()._get_durations(check_leave_type, resource_calendar)

        indian_leaves, leaves_dates_by_employee, public_holidays_date_by_company = self._l10n_in_prepare_sandwich_context()
        if not indian_leaves:
            return result

        for leave in indian_leaves:
            leave_days, hours = result[leave.id]
            if not leave_days or (
                leave.state in ["validate", "validate1"]
                and not self.env.user.has_group("hr_holidays.group_hr_holidays_user")
            ):
                continue
            default_hours = leave._l10n_in_get_default_leave_hours()
            if not leave._l10n_in_is_full_day_request(hours=hours, default_hours=default_hours):
                leave.l10n_in_contains_sandwich_leaves = False
                continue
            updated_days = leave._l10n_in_apply_sandwich_rule(public_holidays_date_by_company, leaves_dates_by_employee)
            if updated_days and updated_days != leave_days:
                updated_hours = (updated_days * (hours / leave_days)) if leave_days else hours
                result[leave.id] = (updated_days, updated_hours)
                leave.l10n_in_contains_sandwich_leaves = True
            else:
                leave.l10n_in_contains_sandwich_leaves = False
        return result