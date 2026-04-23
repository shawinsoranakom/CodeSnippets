def write(self, vals):
        values = vals
        detached_events = self.env['calendar.event']
        recurrence_update_setting = values.pop('recurrence_update', None)
        update_recurrence = recurrence_update_setting in ('all_events', 'future_events') and len(self) == 1 and self.recurrence_id
        break_recurrence = values.get('recurrency') is False

        if any(vals in self._get_recurrent_fields() for vals in values) and not (update_recurrence or values.get('recurrency')):
            raise UserError(_('Unable to save the recurrence with "This Event"'))

        # Check the privacy permissions of the events whose organizer is different from the current user.
        self.filtered(lambda ev: ev.user_id and self.env.user != ev.user_id)._check_calendar_privacy_write_permissions()

        update_alarms = False
        update_time = False
        self._set_videocall_location([values])
        if 'partner_ids' in values:
            values['attendee_ids'] = self._attendees_values(values['partner_ids'])
            update_alarms = True
            if self.videocall_channel_id:
                new_partner_ids = []
                for command in values['partner_ids']:
                    if command[0] == Command.LINK:
                        new_partner_ids.append(command[1])
                    elif command[0] == Command.SET:
                        new_partner_ids.extend(command[2])
                self.videocall_channel_id.add_members(new_partner_ids)

        time_fields = self.env['calendar.event']._get_time_fields()
        if any([values.get(key) for key in time_fields]):
            update_alarms = True
            update_time = True
        if 'alarm_ids' in values:
            update_alarms = True

        if (not recurrence_update_setting or recurrence_update_setting == 'self_only' and len(self) == 1) and 'follow_recurrence' not in values:
            if any({field: values.get(field) for field in time_fields if field in values}):
                values['follow_recurrence'] = False

        previous_attendees = self.attendee_ids

        recurrence_values = {field: values.pop(field) for field in self._get_recurrent_fields() if field in values}
        future_edge_case = recurrence_update_setting == 'future_events' and self == self.recurrence_id.base_event_id
        if update_recurrence:
            if break_recurrence:
                # Update this event
                detached_events |= self._break_recurrence(future=recurrence_update_setting == 'future_events')
            else:
                time_values = {field: values.pop(field) for field in time_fields if field in values}
                if 'access_token' in values:
                    values.pop('access_token')  # prevents copying access_token to other events in recurrency
                if recurrence_update_setting == 'all_events' or future_edge_case:
                    # Update all events: we create a new reccurrence and dismiss the existing events
                    self._rewrite_recurrence(values, time_values, recurrence_values)
                else:
                    # Update future events: trim recurrence, delete remaining events except base event and recreate it
                    # All the recurrent events processing is done within the following method
                    self._update_future_events(values, time_values, recurrence_values)
        else:
            super().write(values)
            self._sync_activities(fields=values.keys())

        # We reapply recurrence for future events and when we add a rrule and 'recurrency' == True on the event
        if recurrence_update_setting not in ['self_only', 'all_events'] and not future_edge_case and not break_recurrence:
            detached_events |= self._apply_recurrence_values(recurrence_values, future=recurrence_update_setting == 'future_events')

        (detached_events & self).active = False
        (detached_events - self).with_context(archive_on_error=True).unlink()

        # Notify attendees if there is an alarm on the modified event, or if there was an alarm
        # that has just been removed, as it might have changed their next event notification
        if not self.env.context.get('dont_notify') and update_alarms:
            self.recurrence_id._setup_alarms(recurrence_update=True)
            if not self.recurrence_id:
                self._setup_alarms()
        attendee_update_events = self.filtered(lambda ev: ev.user_id and ev.user_id != self.env.user)
        if update_time and attendee_update_events:
            # Another user update the event time fields. It should not be auto accepted for the organizer.
            # This prevent weird behavior when a user modified future events time fields and
            # the base event of a recurrence is accepted by the organizer but not the following events
            attendee_update_events.attendee_ids.filtered(lambda att: self.user_id.partner_id == att.partner_id).write({'state': 'needsAction'})

        current_attendees = self.filtered('active').attendee_ids
        skip_attendee_notification = self.env.context.get('skip_attendee_notification')
        if not skip_attendee_notification and 'partner_ids' in values:
            ignore_past_event_attendees = current_attendees.filtered(lambda attendee: attendee.event_id.start < fields.Datetime.now())
            # we send to all partners and not only the new ones
            (current_attendees - previous_attendees - ignore_past_event_attendees)._notify_attendees(
                self.env.ref('calendar.calendar_template_meeting_invitation', raise_if_not_found=False),
                force_send=True,
            )
        if not skip_attendee_notification and not self.env.context.get('is_calendar_event_new') and 'start' in values:
            start_date = fields.Datetime.to_datetime(values.get('start'))
            # Only notify on future events
            if start_date and start_date >= fields.Datetime.now():
                (current_attendees & previous_attendees).with_context(
                    calendar_template_ignore_recurrence=not update_recurrence
                )._notify_attendees(
                    self.env.ref('calendar.calendar_template_meeting_changedate', raise_if_not_found=False),
                    force_send=True,
                )

        # Change base event when the main base event is archived. If it isn't done when trying to modify
        # all events of the recurrence an error can be thrown or all the recurrence can be deleted.
        if values.get("active") is False:
            recurrences = self.env["calendar.recurrence"].search([
                ('base_event_id', 'in', self.ids)
            ])
            recurrences._select_new_base_event()

        return True