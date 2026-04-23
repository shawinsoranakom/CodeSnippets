def unlink(self):
        # Forbid recurrent events unlinking from calendar list view with sync active.
        if self and self._check_microsoft_sync_status():
            synced_events = self._get_synced_events()
            change_from_microsoft = self.env.context.get('dont_notify', False)
            recurrence_deletion = any(ev.recurrency and ev.recurrence_id and ev.follow_recurrence for ev in synced_events)
            if not change_from_microsoft and recurrence_deletion:
                self._forbid_recurrence_update()
        return super().unlink()