def get_next_alarm_date(self, events_by_alarm):
        self.ensure_one()
        now = fields.Datetime.now()
        sorted_alarms = self.alarm_ids.sorted("duration_minutes")
        triggered_alarms = sorted_alarms.filtered(lambda alarm: alarm.id in events_by_alarm)[0]
        event_has_future_alarms = sorted_alarms[0] != triggered_alarms
        next_date = None
        if self.recurrence_id.trigger_id and self.recurrence_id.trigger_id.call_at <= now:
            next_date = self.start - timedelta(minutes=sorted_alarms[0].duration_minutes) \
                if event_has_future_alarms \
                else self.start
        # For recurrent events, when there is no next_date and no trigger in the recurence, set the next
        # date as the date of the next event. This keeps the single alarm alive in the recurrence.
        recurrence_has_no_trigger = self.recurrence_id and not self.recurrence_id.trigger_id
        if recurrence_has_no_trigger and not next_date and len(sorted_alarms) > 0:
            future_recurrent_events = self.recurrence_id.calendar_event_ids.filtered(lambda ev: ev.start > self.start)
            if future_recurrent_events:
                # The next event (minus the alarm duration) will be the next date.
                next_recurrent_event = future_recurrent_events.sorted("start")[0]
                next_date = next_recurrent_event.start - timedelta(minutes=sorted_alarms[0].duration_minutes)
        return next_date