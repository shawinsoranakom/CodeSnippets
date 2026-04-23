def _sync_odoo2microsoft(self):
        if not self:
            return
        if self._active_name:
            records_to_sync = self.filtered(self._active_name)
        else:
            records_to_sync = self
        cancelled_records = self - records_to_sync

        records_to_sync._ensure_attendees_have_email()
        updated_records = records_to_sync._get_synced_events()
        new_records = records_to_sync - updated_records

        for record in cancelled_records._get_synced_events():
            record._microsoft_delete(record._get_organizer(), record.microsoft_id)
        for record in new_records:
            values = record._microsoft_values(self._get_microsoft_synced_fields())
            sender_user = record._get_event_user_m()
            if record._is_microsoft_insertion_blocked(sender_user):
                continue
            if isinstance(values, dict):
                record._microsoft_insert(values)
            else:
                for value in values:
                    record._microsoft_insert(value)
        for record in updated_records.filtered('need_sync_m'):
            values = record._microsoft_values(self._get_microsoft_synced_fields())
            if not values:
                continue
            record._microsoft_patch(record._get_organizer(), record.microsoft_id, values)