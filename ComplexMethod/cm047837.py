def _get_first_available_slot(self, start_datetime, duration, forward=True, leaves_to_ignore=False, extra_leaves_slots=[]):
        """Get the first available interval for the workcenter in `self`.

        The available interval is disjoinct with all other workorders planned on this workcenter, but
        can overlap the time-off of the related calendar (inverse of the working hours).
        Return the first available interval (start datetime, end datetime) or,
        if there is none before 700 days, a tuple error (False, 'error message').

        :param duration: minutes needed to make the workorder (float)
        :param start_datetime: begin the search at this datetime
        :param forward: forward scheduling (search from start_datetime to 700 days after), or backward (from start_datetime to now)
        :param leaves_to_ignore: typically, ignore allocated leave when re-planning a workorder
        :param extra_leaves_slots: extra time slots (start, stop) to consider
        :rtype: tuple
        """
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        max_planning_iterations = max(int(ICP.get_param('mrp.workcenter_max_planning_iterations', '50')), 1)
        resource = self.resource_id
        revert = to_timezone(start_datetime.tzinfo)
        start_datetime = localized(start_datetime)
        get_available_intervals = partial(self.resource_calendar_id._work_intervals_batch, resources=resource, tz=timezone(self.resource_calendar_id.tz))
        workorder_intervals_leaves_domain = [('time_type', '=', 'other')]
        if leaves_to_ignore:
            workorder_intervals_leaves_domain.append(('id', 'not in', leaves_to_ignore.ids))
        get_workorder_intervals = partial(self.resource_calendar_id._leave_intervals_batch, domain=workorder_intervals_leaves_domain, resources=resource, tz=timezone(self.resource_calendar_id.tz))
        extra_leaves_slots_intervals = Intervals([(localized(start), localized(stop), self.env['resource.calendar.attendance']) for start, stop in extra_leaves_slots])

        remaining = duration = max(duration, 1 / 60)
        now = localized(datetime.now())
        delta = timedelta(days=14)
        start_interval, stop_interval = None, None
        for n in range(max_planning_iterations):  # 50 * 14 = 700 days in advance
            if forward:
                date_start = start_datetime + delta * n
                date_stop = date_start + delta
                available_intervals = get_available_intervals(date_start, date_stop)[resource.id]
                workorder_intervals = get_workorder_intervals(date_start, date_stop)[resource.id]
                for start, stop, _records in available_intervals:
                    start_interval = start_interval or start
                    interval_minutes = (stop - start).total_seconds() / 60
                    while (interval := Intervals([(start_interval or start, start + timedelta(minutes=min(remaining, interval_minutes)), _records)])) \
                      and (conflict := interval & workorder_intervals or interval & extra_leaves_slots_intervals):
                        (_start, start, _records) = conflict._items[0]  # restart available interval at conflicting interval stop
                        interval_minutes = (stop - start).total_seconds() / 60
                        start_interval, remaining = start if interval_minutes else None, duration
                    if float_compare(interval_minutes, remaining, precision_digits=3) >= 0:
                        return revert(start_interval), revert(start + timedelta(minutes=remaining))
                    remaining -= interval_minutes
            else:
                # same process but starting from end on reversed intervals
                date_stop = start_datetime - delta * n
                date_start = date_stop - delta
                available_intervals = get_available_intervals(date_start, date_stop)[resource.id]
                available_intervals = reversed(available_intervals)
                workorder_intervals = get_workorder_intervals(date_start, date_stop)[resource.id]
                for start, stop, _records in available_intervals:
                    stop_interval = stop_interval or stop
                    interval_minutes = (stop - start).total_seconds() / 60
                    while (interval := Intervals([(stop - timedelta(minutes=min(remaining, interval_minutes)), stop_interval or stop, _records)])) \
                      and (conflict := interval & workorder_intervals or interval & extra_leaves_slots_intervals):
                        (stop, _stop, _records) = conflict._items[0]  # restart available interval at conflicting interval start
                        interval_minutes = (stop - start).total_seconds() / 60
                        stop_interval, remaining = stop if interval_minutes else None, duration
                    if float_compare(interval_minutes, remaining, precision_digits=3) >= 0:
                        return revert(stop - timedelta(minutes=remaining)), revert(stop_interval)
                    remaining -= interval_minutes
                if date_start <= now:
                    break
        return False, 'No available slot 700 days after the planned start'