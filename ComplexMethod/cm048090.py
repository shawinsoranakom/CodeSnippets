def _get_future_leaves_on(self, accrual_date):
        # As computing future accrual allocation days automatically updates the allocation,
        # We need to create a temporary copy of that allocation to return the difference in number of days
        # to see how much more days will be allocated from now until that date.
        self.ensure_one()
        if not accrual_date or accrual_date <= date.today():
            return 0

        if not (self.accrual_plan_id
                and self.state == 'validate'
                and self.allocation_type == 'accrual'
                and (not self.date_to or self.date_to > accrual_date)
                and (not self.nextcall or self.nextcall <= accrual_date)):
            return 0

        fake_allocation = self.env['hr.leave.allocation'].new(origin=self)
        fake_allocation.sudo()._process_accrual_plans(accrual_date, log=False)
        if self.holiday_status_id.request_unit in ['hour']:
            res = float_round(fake_allocation.number_of_hours_display - self.number_of_hours_display, precision_digits=2)
        else:
            res = round((fake_allocation.number_of_days - self.number_of_days), 2)
        fake_allocation.invalidate_recordset()
        return res