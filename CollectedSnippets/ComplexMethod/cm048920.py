def _l10n_in_apply_sandwich_rule(self, public_holidays_date_by_company, leaves_dates_by_employee):
        self.ensure_one()
        if not (self.request_date_from and self.request_date_to):
            return 0

        date_from = self.request_date_from
        date_to = self.request_date_to
        public_holiday_dates = public_holidays_date_by_company.get(self.company_id, {})
        is_non_working_from = not self._l10n_in_is_working(date_from, public_holiday_dates, self.resource_calendar_id)
        is_non_working_to = not self._l10n_in_is_working(date_to, public_holiday_dates, self.resource_calendar_id)

        if is_non_working_from and is_non_working_to and not any(
            self._l10n_in_is_working(date_from + timedelta(days=x), public_holiday_dates, self.resource_calendar_id)
            for x in range(1, (date_to - date_from).days)
        ):
            return 0

        total_leaves = (date_to - date_from).days + 1
        linked_before, linked_after = self._l10n_in_get_linked_leaves(leaves_dates_by_employee, public_holidays_date_by_company)
        linked_before_leave = linked_before[:1]
        linked_after_leave = linked_after[:1]
        # Only expand the current leave when the linked record starts before it.
        has_previous_link = bool(linked_before_leave and linked_before_leave.request_date_from < date_from)
        has_next_link = bool(linked_after_leave and linked_after_leave.request_date_from > date_to)

        if has_previous_link:
            total_leaves += self._l10n_in_count_adjacent_non_working(
                date_from, public_holiday_dates, self.resource_calendar_id, reverse=True
            )
        elif is_non_working_from:
            total_leaves -= self._l10n_in_count_adjacent_non_working(
                date_from, public_holiday_dates, self.resource_calendar_id, include_start=True,
            )

        if has_next_link:
            total_leaves += self._l10n_in_count_adjacent_non_working(
                date_to, public_holiday_dates, self.resource_calendar_id
            )
        elif is_non_working_to:
            total_leaves = total_leaves - self._l10n_in_count_adjacent_non_working(
                date_to, public_holiday_dates, self.resource_calendar_id, reverse=True, include_start=True,
            )
        return total_leaves