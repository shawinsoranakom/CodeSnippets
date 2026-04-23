def write(self, vals):
        # synchronize calendar events
        res = super().write(vals)
        # protect against loops in case of ill-managed timezones
        if 'date_deadline' in vals and not self.env.context.get('calendar_event_meeting_update') and self.calendar_event_id:
            date_deadline = self[0].date_deadline  # updated, hence all same value
            # also protect against loops in case of ill-managed timezones
            events = self.calendar_event_id.with_context(mail_activity_meeting_update=True)
            user_tz = self.env.context.get('tz') or 'UTC'
            for event in events:
                # allday: just apply diff between dates
                if event.allday and event.start_date != date_deadline:
                    event.start = event.start + (date_deadline - event.start_date)
                # otherwise: we have to check if day did change, based on TZ
                elif not event.allday:
                    # old start in user timezone
                    old_deadline_dt = pytz.utc.localize(event.start).astimezone(pytz.timezone(user_tz))
                    date_diff = date_deadline - old_deadline_dt.date()
                    event.start = event.start + date_diff

        return res