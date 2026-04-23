def _google_values(self):
        # In Google API, all-day events must have their 'dateTime' information set
        # as null and timed events must have their 'date' information set as null.
        # This is mandatory for allowing changing timed events to all-day and vice versa.
        start = {'date': None, 'dateTime': None}
        end = {'date': None, 'dateTime': None}
        if self.allday:
            # For all-day events, 'dateTime' must be set to None to indicate that it's an all-day event.
            # Otherwise, if both 'date' and 'dateTime' are set, Google may not recognize it as an all-day event.
            start['date'] = self.start_date.isoformat()
            end['date'] = (self.stop_date + relativedelta(days=1)).isoformat()
        else:
            # For timed events, 'date' must be set to None to indicate that it's not an all-day event.
            # Otherwise, if both 'date' and 'dateTime' are set, Google may not recognize it as a timed event
            start['dateTime'] = pytz.utc.localize(self.start).isoformat()
            end['dateTime'] = pytz.utc.localize(self.stop).isoformat()
        reminders = [{
            'method': "email" if alarm.alarm_type == "email" else "popup",
            'minutes': alarm.duration_minutes
        } for alarm in self.alarm_ids]

        attendees = self.attendee_ids
        attendee_values = [{
            'email': attendee.partner_id.email_normalized,
            'responseStatus': attendee.state or 'needsAction',
        } for attendee in attendees if attendee.partner_id.email_normalized]
        # We sort the attendees to avoid undeterministic test fails. It's not mandatory for Google.
        attendee_values.sort(key=lambda k: k['email'])
        values = {
            'id': self.google_id,
            'start': start,
            'end': end,
            'summary': self.name,
            'description': self._get_customer_description(),
            'location': self.location or '',
            'guestsCanModify': not self.guests_readonly,
            'organizer': {'email': self.user_id.email, 'self': self.user_id == self.env.user},
            'attendees': attendee_values,
            'extendedProperties': {
                'shared': {
                    '%s_odoo_id' % self.env.cr.dbname: self.id,
                },
            },
            'reminders': {
                'overrides': reminders,
                'useDefault': False,
            }
        }
        if not self.google_id and not self.videocall_location and not self.location:
            values['conferenceData'] = {'createRequest': {'requestId': uuid4().hex}}
        if self.google_id and not self.videocall_location:
            values['conferenceData'] = None
        if self.privacy:
            values['visibility'] = self.privacy
        if self.show_as:
            values['transparency'] = 'opaque' if self.show_as == 'busy' else 'transparent'
        if not self.active:
            values['status'] = 'cancelled'
        if self.user_id and self.user_id != self.env.user and not bool(self.user_id.sudo().google_calendar_token):
            # The organizer is an Odoo user that do not sync his calendar
            values['extendedProperties']['shared']['%s_owner_id' % self.env.cr.dbname] = self.user_id.id
        elif not self.user_id:
            # We can't store on the shared properties in that case without getting a 403. It can happen when
            # the owner is not an Odoo user: We don't store the real owner identity (mail)
            # If we are not the owner, we should change the post values to avoid errors because we don't have
            # write permissions
            # See https://developers.google.com/calendar/concepts/sharing
            keep_keys = ['id', 'summary', 'attendees', 'start', 'end', 'reminders']
            values = {key: val for key, val in values.items() if key in keep_keys}
            # values['extendedProperties']['private] should be used if the owner is not an odoo user
            values['extendedProperties'] = {
                'private': {
                    '%s_odoo_id' % self.env.cr.dbname: self.id,
                },
            }
        return values