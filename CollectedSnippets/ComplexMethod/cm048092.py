def _add_lastcalls(self):
        for allocation in self:
            if allocation.allocation_type != 'accrual':
                continue
            today = fields.Date.today()
            (current_level, current_level_idx) = allocation._get_current_accrual_plan_level_id(today)
            if not allocation.lastcall:
                if not current_level:
                    allocation.lastcall = today
                    allocation.actual_lastcall = allocation.lastcall
                    continue
                allocation.lastcall = max(
                    current_level._get_previous_date(today),
                    allocation.date_from + get_timedelta(current_level.start_count, current_level.start_type)
                )
                allocation.actual_lastcall = allocation.lastcall
            if current_level and not allocation.nextcall:
                accrual_plan = allocation.accrual_plan_id
                allocation.nextcall = current_level._get_next_date(allocation.lastcall)
                if current_level_idx < (len(accrual_plan.level_ids) - 1) and accrual_plan.transition_mode == 'immediately':
                    next_level = accrual_plan.level_ids[current_level_idx + 1]
                    next_level_start = allocation.date_from + get_timedelta(next_level.start_count, next_level.start_type)
                    allocation.nextcall = min(allocation.nextcall, next_level_start)
                # If the expiration date didn't pass (expiration date is in the future)
                expiration_date = allocation.carried_over_days_expiration_date
                if expiration_date and expiration_date > allocation.lastcall:
                    allocation.nextcall = min(allocation.nextcall, expiration_date)