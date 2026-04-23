def _l10n_in_update_neighbors_duration_after_change(self):
        indian_leaves, leaves_dates_by_employee, public_holidays_dates_by_company = self._l10n_in_prepare_sandwich_context()
        if not indian_leaves:
            return
        if all(state in ['refuse', 'cancel'] for state in self.mapped('state')):
            self.l10n_in_contains_sandwich_leaves = False

        linked_before, linked_after = indian_leaves._l10n_in_get_linked_leaves(
            leaves_dates_by_employee, public_holidays_dates_by_company
        )
        neighbors = (linked_before | linked_after) - self
        if not neighbors:
            return

        if any(state in ['validate', 'validate1'] for state in self.mapped('state')):
            neighbors |= self
        # Recompute neighbor durations with the baseline (non-sandwich) logic.
        base_map = super(HrLeave, neighbors)._get_durations(
            check_leave_type=True,
            resource_calendar=None,
        )

        for neighbor in neighbors:
            base_days, base_hours = base_map.get(neighbor.id, (neighbor.number_of_days, neighbor.number_of_hours))
            default_hours = neighbor._l10n_in_get_default_leave_hours()
            if not neighbor._l10n_in_is_full_day_request(hours=base_hours, default_hours=default_hours):
                neighbor.write({
                    'number_of_days': base_days,
                    'number_of_hours': base_hours,
                    'l10n_in_contains_sandwich_leaves': False,
                })
                continue
            updated_days = neighbor._l10n_in_apply_sandwich_rule(
                public_holidays_date_by_company=public_holidays_dates_by_company,
                leaves_dates_by_employee=leaves_dates_by_employee,
            )
            if updated_days and updated_days != base_days:
                new_hours = (updated_days * (base_hours / base_days)) if base_days else base_hours
                neighbor.write({
                    'number_of_days': updated_days,
                    'number_of_hours': new_hours,
                    'l10n_in_contains_sandwich_leaves': True,
                })
            else:
                neighbor.write({
                    'number_of_days': base_days,
                    'number_of_hours': base_hours,
                    'l10n_in_contains_sandwich_leaves': False,
                })