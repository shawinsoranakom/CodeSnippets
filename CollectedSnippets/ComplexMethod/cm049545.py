def _compute_scheduled_date(self):
        for scheduler in self:
            if scheduler.interval_type == 'after_sub':
                date, sign = scheduler.event_id.create_date, 1
            elif scheduler.interval_type in ('before_event', 'after_event_start'):
                date, sign = scheduler.event_id.date_begin, scheduler.interval_type == 'before_event' and -1 or 1
            else:
                date, sign = scheduler.event_id.date_end, scheduler.interval_type == 'after_event' and 1 or -1

            scheduler.scheduled_date = date.replace(microsecond=0) + _INTERVALS[scheduler.interval_unit](sign * scheduler.interval_nbr) if date else False

        next_schedule = self.filtered('scheduled_date').mapped('scheduled_date')
        if next_schedule and (cron := self.env.ref('event.event_mail_scheduler', raise_if_not_found=False)):
            cron._trigger(next_schedule)