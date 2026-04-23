def _setup_alarms(self):
        """ Schedule cron triggers for future events """
        cron = self.env.ref('calendar.ir_cron_scheduler_alarm').sudo()
        alarm_types = self._get_trigger_alarm_types()
        events_to_notify = self.env['calendar.event']
        triggers_by_events = {}
        for event in self:
            existing_trigger = event.recurrence_id.sudo().trigger_id
            for alarm in (alarm for alarm in event.alarm_ids if alarm.alarm_type in alarm_types):
                at = event.start - timedelta(minutes=alarm.duration_minutes)
                create_trigger = not existing_trigger or existing_trigger and existing_trigger.call_at != at
                if create_trigger and (not cron.lastcall or at > cron.lastcall):
                    # Don't trigger for past alarms, they would be skipped by design
                    trigger = cron._trigger(at=at)
                    triggers_by_events[event.id] = trigger.id
            if any(alarm.alarm_type == 'notification' for alarm in event.alarm_ids):
                # filter events before notifying attendees through calendar_alarm_manager
                events_to_notify |= event.filtered(lambda ev: ev.alarm_ids and ev.stop >= fields.Datetime.now())
        if events_to_notify:
            self.env['calendar.alarm_manager']._notify_next_alarm(events_to_notify.partner_ids.ids)
        return triggers_by_events