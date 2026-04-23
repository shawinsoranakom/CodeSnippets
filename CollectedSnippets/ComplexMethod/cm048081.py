def _get_closest_expiring_leaves_date_and_count(self, allocations, remaining_leaves, target_date):
        # Get the expiration date and carryover date of all allocations and compute the closest expiration date
        expiration_dates_per_allocation = defaultdict(lambda: {'expiration_date': fields.Date(), 'carryover_date': fields.Date(), 'carried_over_days_expiration_date': fields.Date()})
        expiration_dates = list()
        carried_over_days_expiration_data = self._get_carried_over_days_expiration_data(allocations, target_date)
        for allocation in allocations:
            expiration_date = allocation.date_to

            accrual_plan_level = allocation.sudo()._get_current_accrual_plan_level_id(target_date)[0]
            carryover_date = False
            if accrual_plan_level and (accrual_plan_level.action_with_unused_accruals == 'lost'
            or accrual_plan_level.carryover_options == 'limited'):
                carryover_date = allocation.sudo()._get_carryover_date(target_date)
                # If carry over date == target date, then add 1 year to carry over date.
                # Rational: for example if carry over date = 01/01 this year and target date = 01/01 this year,
                # then any accrued days on 01/01 this year will have their carry over date 01/01 next year
                # and not 01/01 this year.
                if carryover_date == target_date:
                    carryover_date += relativedelta(years=1)

            carried_over_days_expiration_date = carried_over_days_expiration_data[allocation]['expiration_date']

            expiration_dates.extend([expiration_date, carryover_date, carried_over_days_expiration_date])
            expiration_dates_per_allocation[allocation]['expiration_date'] = expiration_date
            expiration_dates_per_allocation[allocation]['carryover_date'] = carryover_date
            expiration_dates_per_allocation[allocation]['carried_over_days_expiration_date'] = carried_over_days_expiration_date

        expiration_dates = list(filter(lambda date: date is not False, expiration_dates))
        expiration_dates.sort()
        # Compute the number of expiring leaves
        for closest_expiration_date in expiration_dates:
            expiring_leaves_count = 0
            for allocation in allocations:
                expiration_date = expiration_dates_per_allocation[allocation]['expiration_date']
                carryover_date = expiration_dates_per_allocation[allocation]['carryover_date']
                carried_over_days_expiration_date = expiration_dates_per_allocation[allocation]['carried_over_days_expiration_date']

                if expiration_date and expiration_date == closest_expiration_date:
                    expiring_leaves_count += remaining_leaves[allocation]['virtual_remaining_leaves']
                elif carryover_date and carryover_date == closest_expiration_date:
                    accrual_plan_level = allocation.sudo()._get_current_accrual_plan_level_id(target_date)[0]
                    expiring_leaves_count += max(0, remaining_leaves[allocation]['virtual_remaining_leaves'] - accrual_plan_level.postpone_max_days)
                elif carried_over_days_expiration_date and carried_over_days_expiration_date == closest_expiration_date:
                    expiring_leaves_count += carried_over_days_expiration_data[allocation]['no_expiring_days']

            if expiring_leaves_count != 0:
                return closest_expiration_date, expiring_leaves_count

        # No leaves will expire
        return False, 0