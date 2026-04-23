def _get_version_work_entries_values(self, date_start, date_stop):
        start_dt = pytz.utc.localize(date_start) if not date_start.tzinfo else date_start
        end_dt = pytz.utc.localize(date_stop) if not date_stop.tzinfo else date_stop
        version_vals = []
        bypassing_work_entry_type_codes = self._get_bypassing_work_entry_type_codes()

        attendances_by_resource = self.sudo()._get_attendance_intervals(start_dt, end_dt)

        resource_calendar_leaves = self._get_resource_calendar_leaves(start_dt, end_dt)
        # {resource: resource_calendar_leaves}
        leaves_by_resource = defaultdict(lambda: self.env['resource.calendar.leaves'])
        for leave in resource_calendar_leaves:
            leaves_by_resource[leave.resource_id.id] |= leave

        tz_dates = {}
        for version in self:
            employee = version.employee_id
            calendar = version.resource_calendar_id
            resource = employee.resource_id
            # if the version is fully flexible, we refer to the employee's timezone
            tz = pytz.timezone(resource.tz) if version._is_fully_flexible() else pytz.timezone(calendar.tz)
            attendances = attendances_by_resource[resource.id]

            # Other calendars: In case the employee has declared time off in another calendar
            # Example: Take a time off, then a credit time.
            resources_list = [self.env['resource.resource'], resource]
            leave_result = defaultdict(list)
            work_result = defaultdict(list)
            for leave in itertools.chain(leaves_by_resource[False], leaves_by_resource[resource.id]):
                for resource in resources_list:
                    # Global time off is not for this calendar, can happen with multiple calendars in self
                    if resource and leave.calendar_id and leave.calendar_id != calendar and not leave.resource_id:
                        continue
                    tz = tz if tz else pytz.timezone((resource or version).tz)
                    if (tz, start_dt) in tz_dates:
                        start = tz_dates[tz, start_dt]
                    else:
                        start = start_dt.astimezone(tz)
                        tz_dates[tz, start_dt] = start
                    if (tz, end_dt) in tz_dates:
                        end = tz_dates[tz, end_dt]
                    else:
                        end = end_dt.astimezone(tz)
                        tz_dates[tz, end_dt] = end
                    dt0 = leave.date_from.astimezone(tz)
                    dt1 = leave.date_to.astimezone(tz)
                    leave_start_dt = max(start, dt0)
                    leave_end_dt = min(end, dt1)
                    leave_interval = (leave_start_dt, leave_end_dt, leave)
                    leave_interval = version._get_valid_leave_intervals(attendances, leave_interval)
                    if leave_interval:
                        if leave.time_type == 'leave':
                            leave_result[resource.id] += leave_interval
                        else:
                            work_result[resource.id] += leave_interval
            mapped_leaves = {r.id: Intervals(leave_result[r.id], keep_distinct=True) for r in resources_list}
            mapped_worked_leaves = {r.id: Intervals(work_result[r.id], keep_distinct=True) for r in resources_list}

            leaves = mapped_leaves[resource.id]
            worked_leaves = mapped_worked_leaves[resource.id]

            real_attendances = attendances - leaves - worked_leaves
            if not calendar:
                real_leaves = leaves
                real_worked_leaves = worked_leaves
            elif calendar.flexible_hours:
                # Flexible hours case
                # For multi day leaves, we want them to occupy the virtual working schedule 12 AM to average working days
                # For one day leaves, we want them to occupy exactly the time it was taken, for a time off in days
                # this will mean the virtual schedule and for time off in hours the chosen hours
                one_day_leaves = Intervals([l for l in leaves if l[0].date() == l[1].date()], keep_distinct=True)
                one_day_worked_leaves = Intervals([l for l in worked_leaves if l[0].date() == l[1].date()], keep_distinct=True)
                multi_day_leaves = leaves - one_day_leaves
                multi_day_worked_leaves = worked_leaves - one_day_worked_leaves
                static_attendances = calendar._attendance_intervals_batch(
                    start_dt, end_dt, resources=resource, tz=tz)[resource.id]
                real_leaves = (static_attendances & multi_day_leaves) | one_day_leaves
                real_worked_leaves = (static_attendances & multi_day_worked_leaves) | one_day_worked_leaves

            elif version.has_static_work_entries() or not leaves:
                # Empty leaves means empty real_leaves
                real_worked_leaves = attendances - real_attendances - leaves
                real_leaves = attendances - real_attendances - real_worked_leaves
            else:
                # In the case of attendance based versions use regular attendances to generate leave intervals
                static_attendances = calendar._attendance_intervals_batch(
                    start_dt, end_dt, resources=resource, tz=tz)[resource.id]
                real_leaves = static_attendances & leaves
                real_worked_leaves = static_attendances & worked_leaves

            real_attendances = self._get_real_attendances(attendances, leaves, worked_leaves)

            if not version.has_static_work_entries():
                # An attendance based version might have an invalid planning, by definition it may not happen with
                # static work entries.
                # Creating overlapping slots for example might lead to a single work entry.
                # In that case we still create both work entries to indicate a problem (conflicting W E).
                split_attendances = []
                for attendance in real_attendances:
                    if attendance[2] and len(attendance[2]) > 1:
                        split_attendances += [(attendance[0], attendance[1], a) for a in attendance[2]]
                    else:
                        split_attendances += [attendance]
                real_attendances = split_attendances

            # A leave period can be linked to several resource.calendar.leave
            split_leaves = []
            for leave_interval in leaves:
                if leave_interval[2] and len(leave_interval[2]) > 1:
                    split_leaves += [(leave_interval[0], leave_interval[1], l) for l in leave_interval[2]]
                else:
                    split_leaves += [(leave_interval[0], leave_interval[1], leave_interval[2])]
            leaves = split_leaves

            split_worked_leaves = []
            for worked_leave_interval in real_worked_leaves:
                if worked_leave_interval[2] and len(worked_leave_interval[2]) > 1:
                    split_worked_leaves += [(worked_leave_interval[0], worked_leave_interval[1], l) for l in worked_leave_interval[2]]
                else:
                    split_worked_leaves += [(worked_leave_interval[0], worked_leave_interval[1], worked_leave_interval[2])]
            real_worked_leaves = split_worked_leaves

            # Attendances
            version_vals += version._get_real_attendance_work_entry_vals(real_attendances)

            for interval in real_worked_leaves:
                work_entry_type = version._get_interval_leave_work_entry_type(interval, worked_leaves, bypassing_work_entry_type_codes)
                # All benefits generated here are using datetimes converted from the employee's timezone
                version_vals += [dict([
                    ('name', "%s: %s" % (work_entry_type.name, employee.name)),
                    ('date_start', interval[0].astimezone(pytz.utc).replace(tzinfo=None)),
                    ('date_stop', interval[1].astimezone(pytz.utc).replace(tzinfo=None)),
                    ('work_entry_type_id', work_entry_type.id),
                    ('employee_id', employee.id),
                    ('version_id', version.id),
                    ('company_id', version.company_id.id),
                    ('state', 'draft'),
                ] + version._get_more_vals_leave_interval(interval, worked_leaves))]

            leaves_over_attendances = Intervals(leaves, keep_distinct=True) & real_leaves
            for interval in real_leaves:
                # Could happen when a leave is configured on the interface on a day for which the
                # employee is not supposed to work, i.e. no attendance_ids on the calendar.
                # In that case, do try to generate an empty work entry, as this would raise a
                # sql constraint error
                if interval[0] == interval[1]:  # if start == stop
                    continue
                leaves_over_interval = [l for l in leaves_over_attendances if l[0] >= interval[0] and l[1] <= interval[1]]
                for leave_interval in [(l[0], l[1], interval[2]) for l in leaves_over_interval]:
                    leave_entry_type = version._get_interval_leave_work_entry_type(leave_interval, leaves, bypassing_work_entry_type_codes)
                    interval_leaves = [leave for leave in leaves if leave[2].work_entry_type_id.id == leave_entry_type.id]
                    if not interval_leaves:
                        # Maybe the computed leave type is not found. In that case, we use all leaves
                        interval_leaves = leaves
                    interval_start = leave_interval[0].astimezone(pytz.utc).replace(tzinfo=None)
                    interval_stop = leave_interval[1].astimezone(pytz.utc).replace(tzinfo=None)
                    version_vals += [dict([
                        ('name', "%s%s" % (leave_entry_type.name + ": " if leave_entry_type else "", employee.name)),
                        ('date_start', interval_start),
                        ('date_stop', interval_stop),
                        ('work_entry_type_id', leave_entry_type.id),
                        ('employee_id', employee.id),
                        ('company_id', version.company_id.id),
                        ('version_id', version.id),
                    ] + version._get_more_vals_leave_interval(interval, interval_leaves))]
        return version_vals