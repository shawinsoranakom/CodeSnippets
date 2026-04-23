def _check_modify_event_permission(self, values):
        """ Check if event modification attempt by attendee is valid to avoid duplicate events creation. """
        # Edge case: when restarting the synchronization, guests can write 'need_sync=True' on events.
        google_sync_restart = values.get('need_sync') and len(values)
        # Edge case 2: when resetting an account, we must be able to erase the event's google_id.
        skip_event_permission = self.env.context.get('skip_event_permission', False)
        # Edge case 3: check if event is synchronizable in order to make sure the error is worth it.
        is_synchronizable = self._check_values_to_sync(values)
        if google_sync_restart or skip_event_permission or not is_synchronizable:
            return
        if any(event.guests_readonly and self.env.user.id != event.user_id.id for event in self):
            raise ValidationError(
                _("The following event can only be updated by the organizer "
                "according to the event permissions set on Google Calendar.")
            )