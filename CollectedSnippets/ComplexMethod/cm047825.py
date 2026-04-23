def _cal_cost(self, date=False):
        """Returns total cost of time spent on workorder.

        :param datetime date: Only calculate for time_ids that ended before this date
        """
        total = 0
        for workorder in self:
            if workorder._should_estimate_cost():
                duration = workorder.duration_expected / 60
            else:
                intervals = Intervals([
                    [t.date_start, t.date_end, t]
                    for t in workorder.time_ids if t.date_end and (not date or t.date_end < date)
                ])
                duration = sum_intervals(intervals)
            total += duration * (workorder.costs_hour or workorder.workcenter_id.costs_hour)
        return total