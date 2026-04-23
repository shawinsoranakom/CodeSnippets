def _update_attendee_status(self, attendee_ids):
        """ Merge current status from 'attendees_ids' with new attendees values for avoiding their info loss in write().
        Create a dict getting the state of each attendee received from 'attendee_ids' variable and then update their state.
        :param attendee_ids: List of attendee commands carrying a dict with 'partner_id' and 'state' keys in its third position.
        """
        state_by_partner = {}
        for cmd in attendee_ids:
            if len(cmd) == 3 and isinstance(cmd[2], dict) and all(key in cmd[2] for key in ['partner_id', 'state']):
                state_by_partner[cmd[2]['partner_id']] = cmd[2]['state']
        for attendee in self.attendee_ids:
            state_update = state_by_partner.get(attendee.partner_id.id)
            if state_update:
                attendee.state = state_update