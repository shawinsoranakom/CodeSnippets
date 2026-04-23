def _sync_odoo2google(self, google_service: GoogleCalendarService):
        if not self:
            return
        if self._active_name:
            records_to_sync = self.filtered(self._active_name)
        else:
            records_to_sync = self
        cancelled_records = self - records_to_sync

        updated_records = records_to_sync.filtered('google_id')
        new_records = records_to_sync - updated_records
        if self.env.user._get_google_sync_status() != "sync_paused":
            for record in cancelled_records:
                if record.google_id and record.need_sync:
                    record.with_user(record._get_event_user())._google_delete(google_service, record.google_id)
            for record in new_records:
                if record._is_google_insertion_blocked(sender_user=self.env.user):
                    continue
                record.with_user(record._get_event_user())._google_insert(google_service, record._google_values())
            for record in updated_records:
                record.with_user(record._get_event_user())._google_patch(google_service, record.google_id, record._google_values())