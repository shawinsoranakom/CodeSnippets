def _get_unusual_days(self, start_dt, end_dt, company_id=False):
        if not self:
            return {}
        self.ensure_one()
        if not start_dt.tzinfo:
            start_dt = start_dt.replace(tzinfo=utc)
        if not end_dt.tzinfo:
            end_dt = end_dt.replace(tzinfo=utc)

        domain = []
        if company_id:
            domain = [('company_id', 'in', (company_id.id, False))]
        if self.flexible_hours:
            leave_intervals = self._leave_intervals_batch(start_dt, end_dt, domain=domain)[False]
            works = set()
            for start_int, end_int, _ in leave_intervals:
                works.update(start_int.date() + timedelta(days=i) for i in range((end_int.date() - start_int.date()).days + 1))
            return {fields.Date.to_string(day.date()): (day.date() in works) for day in rrule(DAILY, start_dt, until=end_dt)}
        works = {d[0].date() for d in self._work_intervals_batch(start_dt, end_dt, domain=domain)[False]}
        return {fields.Date.to_string(day.date()): (day.date() not in works) for day in rrule(DAILY, start_dt, until=end_dt)}