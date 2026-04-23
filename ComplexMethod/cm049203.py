def _microsoft_values(self, fields_to_sync, initial_values=()):
        values = dict(initial_values)
        if not fields_to_sync:
            return values

        microsoft_guid = self.env['ir.config_parameter'].sudo().get_param('microsoft_calendar.microsoft_guid', False)

        if self.microsoft_recurrence_master_id and 'type' not in values:
            values['seriesMasterId'] = self.microsoft_recurrence_master_id
            values['type'] = 'exception'

        if 'name' in fields_to_sync:
            values['subject'] = self.name or ''

        if 'description' in fields_to_sync:
            values['body'] = {
                'content': self._get_customer_description(),
                'contentType': "html",
            }

        if any(x in fields_to_sync for x in ['allday', 'start', 'date_end', 'stop']):
            if self.allday:
                start = {'dateTime': self.start_date.isoformat(), 'timeZone': 'Europe/London'}
                end = {'dateTime': (self.stop_date + relativedelta(days=1)).isoformat(), 'timeZone': 'Europe/London'}
            else:
                start = {'dateTime': pytz.utc.localize(self.start).isoformat(), 'timeZone': 'Europe/London'}
                end = {'dateTime': pytz.utc.localize(self.stop).isoformat(), 'timeZone': 'Europe/London'}

            values['start'] = start
            values['end'] = end
            values['isAllDay'] = self.allday

        if 'location' in fields_to_sync:
            values['location'] = {'displayName': self.location or ''}

        if not self.location and 'videocall_location' in fields_to_sync and self._need_video_call():
            values['isOnlineMeeting'] = True
            values['onlineMeetingProvider'] = 'teamsForBusiness'
        else:
            values['isOnlineMeeting'] = False

        if 'alarm_ids' in fields_to_sync:
            alarm_id = self.alarm_ids.filtered(lambda a: a.alarm_type == 'notification')[:1]
            values['isReminderOn'] = bool(alarm_id)
            values['reminderMinutesBeforeStart'] = alarm_id.duration_minutes

        if 'user_id' in fields_to_sync:
            values['organizer'] = {'emailAddress': {'address': self.user_id.email or '', 'name': self.user_id.display_name or ''}}
            values['isOrganizer'] = self.user_id == self.env.user

        if 'attendee_ids' in fields_to_sync:
            attendees = self.attendee_ids.filtered(lambda att: att.partner_id not in self.user_id.partner_id)
            values['attendees'] = [
                {
                    'emailAddress': {'address': attendee.email or '', 'name': attendee.display_name or ''},
                    'status': {'response': self._get_attendee_status_o2m(attendee)}
                } for attendee in attendees]

        if 'privacy' in fields_to_sync or 'show_as' in fields_to_sync:
            values['showAs'] = self.show_as
            sensitivity_o2m = {
                'public': 'normal',
                'private': 'private',
                'confidential': 'confidential',
            }
            # Set default privacy in event according to the organizer's calendar default privacy if defined.
            if self.user_id:
                sensitivity_o2m[False] = sensitivity_o2m.get(self.user_id.calendar_default_privacy)
            else:
                sensitivity_o2m[False] = 'normal'
            values['sensitivity'] = sensitivity_o2m.get(self.privacy)

        if 'active' in fields_to_sync and not self.active:
            values['isCancelled'] = True

        if values.get('type') == 'seriesMaster':
            recurrence = self.recurrence_id
            pattern = {
                'interval': recurrence.interval
            }
            if recurrence.rrule_type in ['daily', 'weekly']:
                pattern['type'] = recurrence.rrule_type
            else:
                prefix = 'absolute' if recurrence.month_by == 'date' else 'relative'
                pattern['type'] = recurrence.rrule_type and prefix + recurrence.rrule_type.capitalize()

            if recurrence.month_by == 'date':
                pattern['dayOfMonth'] = recurrence.day

            if recurrence.month_by == 'day' or recurrence.rrule_type == 'weekly':
                pattern['daysOfWeek'] = [
                    weekday_name for weekday_name, weekday in {
                        'monday': recurrence.mon,
                        'tuesday': recurrence.tue,
                        'wednesday': recurrence.wed,
                        'thursday': recurrence.thu,
                        'friday': recurrence.fri,
                        'saturday': recurrence.sat,
                        'sunday': recurrence.sun,
                    }.items() if weekday]
                pattern['firstDayOfWeek'] = 'sunday'

            if recurrence.rrule_type == 'monthly' and recurrence.month_by == 'day':
                byday_selection = {
                    '1': 'first',
                    '2': 'second',
                    '3': 'third',
                    '4': 'fourth',
                    '-1': 'last',
                }
                pattern['index'] = byday_selection[recurrence.byday]

            dtstart = recurrence.dtstart or fields.Datetime.now()
            rule_range = {
                'startDate': (dtstart.date()).isoformat()
            }

            if recurrence.end_type == 'count':  # e.g. stop after X occurence
                rule_range['numberOfOccurrences'] = min(recurrence.count, MAX_RECURRENT_EVENT)
                rule_range['type'] = 'numbered'
            elif recurrence.end_type == 'forever':
                rule_range['numberOfOccurrences'] = MAX_RECURRENT_EVENT
                rule_range['type'] = 'numbered'
            elif recurrence.end_type == 'end_date':  # e.g. stop after 12/10/2020
                rule_range['endDate'] = recurrence.until.isoformat()
                rule_range['type'] = 'endDate'

            values['recurrence'] = {
                'pattern': pattern,
                'range': rule_range
            }

        return values