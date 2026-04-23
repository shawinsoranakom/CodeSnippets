def _get_consumed_leaves(self, leave_types, target_date=False, ignore_future=False):
        """ This method won't call `_get_future_leaves_on` for the allocations contained by this variable (it will only use the current value of
            the `number_of_days` of the allocation, alias `number_of_hours_display`)

            `precomputed_allocations`: context variable (recordset) which can be used to pass allocation that are considered to be already computed
        """
        employees = self or self._get_contextual_employee()
        leaves_domain = [
            ('holiday_status_id', 'in', leave_types.ids),
            ('employee_id', 'in', employees.ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
        ]
        if self.env.context.get('ignored_leave_ids'):
            leaves_domain.append(('id', 'not in', self.env.context.get('ignored_leave_ids')))

        if not target_date:
            target_date = fields.Date.today()
        if ignore_future:
            leaves_domain.append(('date_from', '<=', target_date))
        leaves = self.env['hr.leave'].search(leaves_domain)
        leaves_per_employee_type = defaultdict(lambda: defaultdict(lambda: self.env['hr.leave']))
        for leave in leaves:
            leaves_per_employee_type[leave.employee_id][leave.holiday_status_id] |= leave

        allocations = self.env['hr.leave.allocation'].with_context(active_test=False).search([
            ('employee_id', 'in', employees.ids),
            ('holiday_status_id', 'in', leave_types.ids),
            ('state', '=', 'validate'),
        ])
        allocations_per_employee_type = defaultdict(lambda: defaultdict(lambda: self.env['hr.leave.allocation']))
        for allocation in allocations:
            allocations_per_employee_type[allocation.employee_id][allocation.holiday_status_id] |= allocation

        # _get_consumed_leaves returns a tuple of two dictionnaries.
        # 1) The first is a dictionary to map the number of days/hours of leaves taken per allocation
        # The structure is the following:
        # - KEYS:
        # allocation_leaves_consumed
        #  |--employee_id
        #      |--holiday_status_id
        #          |--allocation
        #              |--virtual_leaves_taken
        #              |--leaves_taken
        #              |--virtual_remaining_leaves
        #              |--remaining_leaves
        #              |--max_leaves
        #              |--accrual_bonus
        # - VALUES:
        # Integer representing the number of (virtual) remaining leaves, (virtual) leaves taken or max leaves
        # for each allocation.
        # leaves_taken and remaining_leaves only take into account validated leaves, while the "virtual" equivalent are
        # also based on leaves in "confirm" or "validate1" state.
        # Accrual bonus gives the amount of additional leaves that will have been granted at the given
        # target_date in comparison to today.
        # The unit is in hour or days depending on the leave type request unit
        # 2) The second is a dictionary mapping the remaining days per employee and per leave type that are either
        # not taken into account by the allocations, mainly because accruals don't take future leaves into account.
        # This is used to warn the user if the leaves they takes bring them above their available limit.
        # - KEYS:
        # allocation_leaves_consumed
        #  |--employee_id
        #      |--holiday_status_id
        #          |--to_recheck_leaves
        #          |--excess_days
        #          |--exceeding_duration
        # - VALUES:
        # "to_recheck_leaves" stores every leave that is not yet taken into account by the "allocation_leaves_consumed" dictionary.
        # "excess_days" represents the excess amount that somehow isn't taken into account by the first dictionary.
        # "exceeding_duration" sum up the to_recheck_leaves duration and compares it to the maximum allocated for that time period.
        allocations_leaves_consumed = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0))))

        to_recheck_leaves_per_leave_type = defaultdict(lambda:
            defaultdict(lambda: {
                'excess_days': defaultdict(lambda: {
                    'amount': 0,
                    'is_virtual': True,
                }),
                'exceeding_duration': 0,
                'to_recheck_leaves': self.env['hr.leave']
            })
        )
        precomputed_allocations = self.env.context.get('precomputed_allocations')
        for allocation in allocations:
            allocation_data = allocations_leaves_consumed[allocation.employee_id][allocation.holiday_status_id][allocation]
            precomputed = False
            if precomputed_allocations:
                if allocation.id in precomputed_allocations.ids:
                    allocation = precomputed_allocations.filtered(lambda alloc: alloc._origin.id == allocation.id)[0]
                    precomputed = True
            future_leaves = 0
            if allocation.allocation_type == 'accrual' and not precomputed:
                future_leaves = allocation._get_future_leaves_on(target_date)
            max_leaves = allocation.number_of_hours_display\
                if allocation.holiday_status_id.request_unit in ['hour']\
                else allocation.number_of_days_display
            max_leaves += future_leaves
            allocation_data.update({
                'max_leaves': max_leaves,
                'accrual_bonus': future_leaves,
                'virtual_remaining_leaves': max_leaves,
                'remaining_leaves': max_leaves,
                'leaves_taken': 0,
                'virtual_leaves_taken': 0,
            })

        for employee in employees:
            for leave_type in leave_types:
                allocations_with_date_to = self.env['hr.leave.allocation']
                allocations_without_date_to = self.env['hr.leave.allocation']
                for leave_allocation in allocations_per_employee_type[employee][leave_type]:
                    if leave_allocation.date_to:
                        allocations_with_date_to |= leave_allocation
                    else:
                        allocations_without_date_to |= leave_allocation
                # Defines the order in which allocation will be used to take the leaves in priority
                sorted_leave_allocations = (
                    allocations_with_date_to.sorted(key='date_to') +
                    allocations_without_date_to.filtered(lambda alloc: alloc.allocation_type == 'accrual') +
                    allocations_without_date_to.filtered(lambda alloc: alloc.allocation_type == 'regular'))

                if leave_type.request_unit in ['day', 'half_day']:
                    leave_duration_field = 'number_of_days'
                    leave_unit = 'days'
                else:
                    leave_duration_field = 'number_of_hours'
                    leave_unit = 'hours'

                leave_type_data = allocations_leaves_consumed[employee][leave_type]
                for leave in leaves_per_employee_type[employee][leave_type].sorted('date_from'):
                    leave_duration = leave[leave_duration_field]
                    skip_excess = False

                    if leave.date_from.date() > target_date and sorted_leave_allocations.filtered(lambda a:
                        a.allocation_type == 'accrual' and
                        (not a.date_to or a.date_to >= target_date) and
                        a.date_from <= leave.date_to.date()
                    ):
                        to_recheck_leaves_per_leave_type[employee][leave_type]['to_recheck_leaves'] |= leave
                        skip_excess = True
                        continue

                    if leave_type.requires_allocation:
                        for allocation in sorted_leave_allocations:
                            # We don't want to include future leaves linked to accruals into the total count of available leaves.
                            # However, we'll need to check if those leaves take more than what will be accrued in total of those days
                            # to give a warning if the total exceeds what will be accrued.
                            if allocation.date_from > leave.date_to.date() or (allocation.date_to and allocation.date_to < leave.date_from.date()):
                                continue
                            interval_start = max(
                                leave.date_from,
                                datetime.combine(allocation.date_from, time.min)
                            )
                            interval_end = min(
                                leave.date_to,
                                datetime.combine(allocation.date_to, time.max)
                                if allocation.date_to else leave.date_to
                            )
                            duration = leave[leave_duration_field]
                            if leave.date_from != interval_start or leave.date_to != interval_end:
                                duration_info = employee._get_calendar_attendances(interval_start.replace(tzinfo=pytz.UTC), interval_end.replace(tzinfo=pytz.UTC))
                                duration = duration_info['hours' if leave_unit == 'hours' else 'days']
                            max_allowed_duration = min(
                                duration,
                                leave_type_data[allocation]['virtual_remaining_leaves']
                            )

                            if not max_allowed_duration:
                                continue

                            allocated_time = min(max_allowed_duration, leave_duration)
                            leave_type_data[allocation]['virtual_leaves_taken'] += allocated_time
                            leave_type_data[allocation]['virtual_remaining_leaves'] -= allocated_time
                            if leave.state == 'validate':
                                leave_type_data[allocation]['leaves_taken'] += allocated_time
                                leave_type_data[allocation]['remaining_leaves'] -= allocated_time

                            leave_duration -= allocated_time
                            if not leave_duration:
                                break
                        if round(leave_duration, 2) > 0 and not skip_excess:
                            to_recheck_leaves_per_leave_type[employee][leave_type]['excess_days'][leave.date_to.date()] = {
                                'amount': leave_duration,
                                'is_virtual': leave.state != 'validate',
                                'leave_id': leave.id,
                            }
                    else:
                        if leave_unit == 'hours':
                            allocated_time = leave.number_of_hours
                        else:
                            allocated_time = leave.number_of_days
                        leave_type_data[False]['virtual_leaves_taken'] += allocated_time
                        leave_type_data[False]['virtual_remaining_leaves'] = 0
                        leave_type_data[False]['remaining_leaves'] = 0
                        if leave.state == 'validate':
                            leave_type_data[False]['leaves_taken'] += allocated_time
        for employee in to_recheck_leaves_per_leave_type:
            for leave_type in to_recheck_leaves_per_leave_type[employee]:
                content = to_recheck_leaves_per_leave_type[employee][leave_type]
                consumed_content = allocations_leaves_consumed[employee][leave_type]
                if content['to_recheck_leaves']:
                    date_to_simulate = max(content['to_recheck_leaves'].mapped('date_from')).date()
                    latest_accrual_bonus = 0
                    date_accrual_bonus = 0
                    virtual_remaining = 0
                    additional_leaves_duration = 0
                    for allocation in consumed_content:
                        latest_accrual_bonus += allocation and allocation._get_future_leaves_on(date_to_simulate)
                        date_accrual_bonus += consumed_content[allocation]['accrual_bonus']
                        virtual_remaining += consumed_content[allocation]['virtual_remaining_leaves']
                    for leave in content['to_recheck_leaves']:
                        additional_leaves_duration += leave.number_of_hours if leave_type.request_unit == 'hour' else leave.number_of_days
                    latest_remaining = virtual_remaining - date_accrual_bonus + latest_accrual_bonus
                    content['exceeding_duration'] = round(min(0, latest_remaining - additional_leaves_duration), 2)

        return (allocations_leaves_consumed, to_recheck_leaves_per_leave_type)