def _cancel_work_entry_conflict(self):
        """
        Creates a leave work entry for each hr.leave in self.
        Check overlapping work entries with self.
        Work entries completely included in a leave are archived.
        e.g.:
            |----- work entry ----|---- work entry ----|
                |------------------- hr.leave ---------------|
                                    ||
                                    vv
            |----* work entry ****|
                |************ work entry leave --------------|
        """
        if not self:
            return

        # 1. Create a work entry for each leave
        work_entries_vals_list = []
        for leave in self:
            contracts = leave.employee_id.sudo()._get_versions_with_contract_overlap_with_period(leave.date_from.date(), leave.date_to.date())
            for contract in contracts:
                # Generate only if it has aleady been generated
                if leave.date_to >= contract.date_generated_from and leave.date_from <= contract.date_generated_to:
                    work_entries_vals_list += contracts._get_work_entries_values(
                        datetime.combine(leave.date_from, time.min),
                        datetime.combine(leave.date_to, time.max),
                    )

        work_entries_vals_list = self.env['hr.version']._generate_work_entries_postprocess(work_entries_vals_list)
        new_leave_work_entries = self.env['hr.work.entry'].create(work_entries_vals_list)

        if new_leave_work_entries:
            # 2. Fetch overlapping work entries, grouped by employees
            start = min(self.mapped('date_from'), default=False)
            stop = max(self.mapped('date_to'), default=False)
            work_entry_groups = self.env['hr.work.entry']._read_group([
                ('date', '<=', stop),
                ('date', '>=', start),
                ('employee_id', 'in', self.employee_id.ids),
            ], ['employee_id'], ['id:recordset'])
            work_entries_by_employee = {
                employee.id: work_entries
                for employee, work_entries in work_entry_groups
            }

            # 3. Archive work entries included in leaves
            included = self.env['hr.work.entry']
            overlappping = self.env['hr.work.entry']
            for work_entries in work_entries_by_employee.values():
                # Work entries for this employee
                new_employee_work_entries = work_entries & new_leave_work_entries
                previous_employee_work_entries = work_entries - new_leave_work_entries

                # Build intervals from work entries
                leave_intervals = new_employee_work_entries._to_intervals()
                conflicts_intervals = previous_employee_work_entries._to_intervals()

                # Compute intervals completely outside any leave
                # Intervals are outside, but associated records are overlapping.
                outside_intervals = conflicts_intervals - leave_intervals

                overlappping |= self.env['hr.work.entry']._from_intervals(outside_intervals)
                included |= previous_employee_work_entries - overlappping
            overlappping.filtered(lambda entry: entry.state != 'validated').write({'leave_id': False})
            included.filtered(lambda entry: entry.state != 'validated').write({'active': False})