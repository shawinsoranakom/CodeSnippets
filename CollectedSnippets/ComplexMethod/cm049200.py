def _microsoft_to_odoo_values(self, microsoft_event, default_reminders=(), default_values=None, with_ids=False):
        if microsoft_event.is_cancelled():
            return {'active': False}

        sensitivity_o2m = {
            'normal': 'public',
            'private': 'private',
            'confidential': 'confidential',
        }

        commands_attendee, commands_partner = self._odoo_attendee_commands_m(microsoft_event)
        timeZone_start = pytz.timezone(microsoft_event.start.get('timeZone'))
        timeZone_stop = pytz.timezone(microsoft_event.end.get('timeZone'))
        start = parse(microsoft_event.start.get('dateTime')).astimezone(timeZone_start).replace(tzinfo=None)
        if microsoft_event.isAllDay:
            stop = parse(microsoft_event.end.get('dateTime')).astimezone(timeZone_stop).replace(tzinfo=None) - relativedelta(days=1)
        else:
            stop = parse(microsoft_event.end.get('dateTime')).astimezone(timeZone_stop).replace(tzinfo=None)
        values = default_values or {}
        values.update({
            'name': microsoft_event.subject or _("(No title)"),
            'description': microsoft_event.body and microsoft_event.body['content'],
            'location': microsoft_event.location and microsoft_event.location.get('displayName') or False,
            'user_id': microsoft_event.owner_id(self.env),
            'privacy': sensitivity_o2m.get(microsoft_event.sensitivity, False),
            'attendee_ids': commands_attendee,
            'allday': microsoft_event.isAllDay,
            'start': start,
            'stop': stop,
            'show_as': 'free' if microsoft_event.showAs == 'free' else 'busy',
            'recurrency': microsoft_event.is_recurrent()
        })
        if commands_partner:
            # Add partner_commands only if set from Microsoft. The write method on calendar_events will
            # override attendee commands if the partner_ids command is set but empty.
            values['partner_ids'] = commands_partner

        if microsoft_event.is_recurrent() and not microsoft_event.is_recurrence():
            # Propagate the follow_recurrence according to the Outlook result
            values['follow_recurrence'] = not microsoft_event.is_recurrence_outlier()

        # if a videocall URL is provided with the Outlook event, use it
        if microsoft_event.isOnlineMeeting and microsoft_event.onlineMeeting.get("joinUrl"):
            values['videocall_location'] = microsoft_event.onlineMeeting["joinUrl"]
        else:
            # if a location is a URL matching a specific pattern (i.e a URL to access to a videocall),
            # copy it in the 'videocall_location' instead
            if values['location'] and any(re.match(p, values['location']) for p in VIDEOCALL_URL_PATTERNS):
                values['videocall_location'] = values['location']
                values['location'] = False

        if with_ids:
            values['microsoft_id'] = microsoft_event.id
            values['ms_universal_event_id'] = microsoft_event.iCalUId


        if microsoft_event.is_recurrent():
            values['microsoft_recurrence_master_id'] = microsoft_event.seriesMasterId

        alarm_commands = self._odoo_reminders_commands_m(microsoft_event)
        if alarm_commands:
            values['alarm_ids'] = alarm_commands

        return values