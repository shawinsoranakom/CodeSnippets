def write(self, vals):
        google_service = GoogleCalendarService(self.env['google.service'])
        synced_fields = self._get_google_synced_fields()
        if 'need_sync' not in vals and vals.keys() & synced_fields and not self.env.user.google_synchronization_stopped:
            vals['need_sync'] = True

        result = super().write(vals)
        if self.env.user._get_google_sync_status() != "sync_paused":
            for record in self:
                if record.need_sync and record.google_id:
                    record.with_user(record._get_event_user())._google_patch(google_service, record.google_id, record._google_values(), timeout=3)

        return result