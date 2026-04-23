def _odoo_values(self, google_event, default_reminders=()):
        if google_event.is_cancelled():
            return {'active': False}

        # default_reminders is never () it is set to google's default reminder (30 min before)
        # we need to check 'useDefault' for the event to determine if we have to use google's
        # default reminder or not
        reminder_command = google_event.reminders.get('overrides')
        if not reminder_command:
            reminder_command = google_event.reminders.get('useDefault') and default_reminders or ()
        alarm_commands = self._odoo_reminders_commands(reminder_command)
        attendee_commands, partner_commands = self._odoo_attendee_commands(google_event)
        related_event = self.search([('google_id', '=', google_event.id)], limit=1)
        name = google_event.summary or related_event and related_event.name or _("(No title)")
        values = {
            'name': name,
            'description': google_event.description and tools.html_sanitize(google_event.description),
            'location': google_event.location,
            'user_id': google_event.owner(self.env).id,
            'privacy': google_event.visibility or False,
            'attendee_ids': attendee_commands,
            'alarm_ids': alarm_commands,
            'recurrency': google_event.is_recurrent(),
            'videocall_location': google_event.get_meeting_url(),
            'show_as': 'free' if google_event.is_available() else 'busy',
            'guests_readonly': not bool(google_event.guestsCanModify)
        }
        # Remove 'videocall_location' when not sent by Google, otherwise the local videocall will be discarded.
        if not values.get('videocall_location'):
            values.pop('videocall_location', False)
        if partner_commands:
            # Add partner_commands only if set from Google. The write method on calendar_events will
            # override attendee commands if the partner_ids command is set but empty.
            values['partner_ids'] = partner_commands
        if not google_event.is_recurrence():
            values['google_id'] = google_event.id
        if google_event.is_recurrent() and not google_event.is_recurrence():
            # Propagate the follow_recurrence according to the google result
            values['follow_recurrence'] = google_event.is_recurrence_follower()
        if google_event.start.get('dateTime'):
            # starting from python3.7, use the new [datetime, date].fromisoformat method
            start = parse(google_event.start.get('dateTime')).astimezone(pytz.utc).replace(tzinfo=None)
            stop = parse(google_event.end.get('dateTime')).astimezone(pytz.utc).replace(tzinfo=None)
            values['allday'] = False
        else:
            start = parse(google_event.start.get('date'))
            stop = parse(google_event.end.get('date')) - relativedelta(days=1)
            # Stop date should be exclusive as defined here https://developers.google.com/calendar/v3/reference/events#resource
            # but it seems that's not always the case for old event
            if stop < start:
                stop = parse(google_event.end.get('date'))
            values['allday'] = True
        if related_event['start'] != start:
            values['start'] = start
        if related_event['stop'] != stop:
            values['stop'] = stop
        return values