def write(self, vals):
        recurrence_update_setting = vals.get('recurrence_update')
        if recurrence_update_setting in ('all_events', 'future_events') and len(self) == 1:
            vals = dict(vals, need_sync=False)
        notify_context = self.env.context.get('dont_notify', False)
        if not notify_context and ([self.env.user.id != record.user_id.id for record in self]):
            self._check_modify_event_permission(vals)
        res = super(CalendarEvent, self.with_context(dont_notify=notify_context)).write(vals)
        if recurrence_update_setting == 'all_events' and len(self) == 1 and vals.keys() & self._get_google_synced_fields():
            self.recurrence_id.need_sync = True
        return res