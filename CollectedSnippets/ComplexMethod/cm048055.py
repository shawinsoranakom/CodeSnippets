def write(self, vals):
        specific_contracts = self.env['hr.version']
        if any(field in vals for field in ['contract_date_start', 'contract_date_end', 'date_version', 'resource_calendar_id']):
            all_new_leave_origin = []
            all_new_leave_vals = []
            leaves_state = {}
            try:
                for contract in self:
                    resource_calendar_id = vals.get('resource_calendar_id', contract.resource_calendar_id.id)
                    extra_domain = [('resource_calendar_id', '!=', resource_calendar_id)] if resource_calendar_id else None
                    leaves = contract._get_leaves(
                        extra_domain=extra_domain
                    )
                    for leave in leaves:
                        super(HrVersion, contract).write(vals)
                        overlapping_contracts = self._check_overlapping_contract(leave)
                        if not overlapping_contracts:
                            continue
                        leaves_state = self._refuse_leave(leave, leaves_state)
                        specific_contracts += contract
                        all_new_leave_origin, all_new_leave_vals = self._populate_all_new_leave_vals_from_split_leave(
                            all_new_leave_origin, all_new_leave_vals, overlapping_contracts, leave, leaves_state)
                if all_new_leave_vals:
                    self._create_all_new_leave(all_new_leave_origin, all_new_leave_vals)
            except ValidationError:
                # In case a validation error is thrown due to holiday creation with the new resource calendar (which can
                # increase their duration), we catch this error to display a more meaningful error message.
                raise ValidationError(self.env._("Changing the contract on this employee changes their working schedule in a period "
                                        "they already took leaves. Changing this working schedule changes the duration of "
                                        "these leaves in such a way the employee no longer has the required allocation for "
                                        "them. Please review these leaves and/or allocations before changing the contract."))
        return super(HrVersion, self - specific_contracts).write(vals)