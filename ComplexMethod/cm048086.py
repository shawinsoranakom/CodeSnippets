def _compute_accrual_plan_id(self):
        accrual_allocations = self.filtered(lambda alloc: alloc.allocation_type == 'accrual' and not alloc.accrual_plan_id and alloc.holiday_status_id)
        accruals_read_group = self.env['hr.leave.accrual.plan']._read_group(
            [('time_off_type_id', 'in', accrual_allocations.holiday_status_id.ids)],
            ['time_off_type_id'],
            ['id:array_agg'],
        )
        accruals_dict = {time_off_type.id: ids for time_off_type, ids in accruals_read_group}
        for allocation in self:
            if (allocation.allocation_type == 'regular' and allocation.accrual_plan_id) or allocation.accrual_plan_id.time_off_type_id.id not in (False, allocation.holiday_status_id.id):
                allocation.accrual_plan_id = False
            if allocation.allocation_type == 'accrual' and not allocation.accrual_plan_id:
                if allocation.holiday_status_id:
                    allocation.accrual_plan_id = accruals_dict.get(allocation.holiday_status_id.id, [False])[0]