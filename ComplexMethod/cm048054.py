def create(self, vals_list):
        all_new_leave_origin = []
        all_new_leave_vals = []
        leaves_state = {}
        created_versions = self.env['hr.version']
        for vals in vals_list:
            if not 'employee_id' in vals or not 'resource_calendar_id' in vals:
                created_versions |= super().create(vals)
                continue
            leaves = self._get_leaves_from_vals(vals)
            is_created = False
            for leave in leaves:
                leaves_state = self._refuse_leave(leave, leaves_state) if leave.request_date_from < vals['contract_date_start'] else self._set_leave_draft(leave, leaves_state)
                if not is_created:
                    created_versions |= super().create([vals])
                    is_created = True
                overlapping_contracts = self._check_overlapping_contract(leave)
                if not overlapping_contracts:
                    # When the leave is set to draft
                    leave._compute_date_from_to()
                    continue
                all_new_leave_origin, all_new_leave_vals = self._populate_all_new_leave_vals_from_split_leave(
                    all_new_leave_origin, all_new_leave_vals, overlapping_contracts, leave, leaves_state)
            # TODO FIXME
            # to keep creation order, not ideal but ok for now.
            if not is_created:
                created_versions |= super().create([vals])
        try:
            if all_new_leave_vals:
                self._create_all_new_leave(all_new_leave_origin, all_new_leave_vals)
        except ValidationError:
            # In case a validation error is thrown due to holiday creation with the new resource calendar (which can
            # increase their duration), we catch this error to display a more meaningful error message.
            raise ValidationError(
                self.env._("Changing the contract on this employee changes their working schedule in a period "
                           "they already took leaves. Changing this working schedule changes the duration of "
                           "these leaves in such a way the employee no longer has the required allocation for "
                           "them. Please review these leaves and/or allocations before changing the contract."))
        return created_versions