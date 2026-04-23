def _write_from_google(self, gevent, vals):
        current_rrule = self.rrule
        current_parsed_rrule = self._rrule_parse(current_rrule, self.dtstart)
        # event_tz is written on event in Google but on recurrence in Odoo
        vals['event_tz'] = gevent.start.get('timeZone')
        super()._write_from_google(gevent, vals)

        base_event_time_fields = ['start', 'stop', 'allday']
        new_event_values = self.env["calendar.event"]._odoo_values(gevent)
        new_parsed_rrule = self._rrule_parse(self.rrule, self.dtstart)
        # We update the attendee status for all events in the recurrence
        google_attendees = gevent.attendees or []
        emails = [a.get('email') for a in google_attendees]
        partners = self._get_sync_partner(emails)
        existing_attendees = self.calendar_event_ids.attendee_ids
        for attendee in zip(emails, partners, google_attendees):
            email = attendee[0]
            if email in existing_attendees.mapped('email'):
                # Update existing attendees
                existing_attendees.filtered(lambda att: att.email == email).write({'state': attendee[2].get('responseStatus')})
            else:
                # Create new attendees
                if attendee[2].get('self'):
                    partner = self.env.user.partner_id
                elif attendee[1]:
                    partner = attendee[1]
                else:
                    continue
                self.calendar_event_ids.write({'attendee_ids': [(0, 0, {'state': attendee[2].get('responseStatus'), 'partner_id': partner.id})]})
                if attendee[2].get('displayName') and not partner.name:
                    partner.name = attendee[2].get('displayName')

        organizers_partner_ids = [event.user_id.partner_id for event in self.calendar_event_ids if event.user_id]
        for odoo_attendee_email in set(existing_attendees.mapped('email')):
            # Sometimes, several partners have the same email. Remove old attendees except organizer, otherwise the events will disappear.
            if email_normalize(odoo_attendee_email) not in emails:
                attendees = existing_attendees.exists().filtered(lambda att: att.email == email_normalize(odoo_attendee_email) and att.partner_id not in organizers_partner_ids)
                self.calendar_event_ids.write({'need_sync': False, 'partner_ids': [Command.unlink(att.partner_id.id) for att in attendees]})

        old_event_values = self.base_event_id and self.base_event_id.read(base_event_time_fields)[0]
        if old_event_values and any(new_event_values.get(key) and new_event_values[key] != old_event_values[key] for key in base_event_time_fields):
            # we need to recreate the recurrence, time_fields were modified.
            base_event_id = self.base_event_id
            non_equal_values = [
                (key, old_event_values[key] and old_event_values[key].strftime('%m/%d/%Y, %H:%M:%S'), '-->',
                      new_event_values[key] and new_event_values[key].strftime('%m/%d/%Y, %H:%M:%S')
                 ) for key in ['start', 'stop'] if new_event_values[key] != old_event_values[key]
            ]
            log_msg = f"Recurrence {self.id} {self.rrule} has all events ({len(self.calendar_event_ids.ids)})  deleted because of base event value change: {non_equal_values}"
            _logger.info(log_msg)
            # We archive the old events to recompute the recurrence. These events are already deleted on Google side.
            # We can't call _cancel because events without user_id would not be deleted
            (self.calendar_event_ids - base_event_id).google_id = False
            (self.calendar_event_ids - base_event_id).unlink()
            base_event_id.with_context(dont_notify=True).write(dict(new_event_values, google_id=False, need_sync=False))
            if new_parsed_rrule == current_parsed_rrule:
                # if the rrule has changed, it will be recalculated below
                # There is no detached event now
                self.with_context(dont_notify=True)._apply_recurrence()
        else:
            time_fields = (
                    self.env["calendar.event"]._get_time_fields()
                    | self.env["calendar.event"]._get_recurrent_fields()
            )
            # We avoid to write time_fields because they are not shared between events.
            self._write_events(dict({
                field: value
                for field, value in new_event_values.items()
                if field not in time_fields
                }, need_sync=False)
            )

        # We apply the rrule check after the time_field check because the google_id are generated according
        # to base_event start datetime.
        if new_parsed_rrule != current_parsed_rrule:
            detached_events = self._apply_recurrence()
            detached_events.google_id = False
            log_msg = f"Recurrence #{self.id} | current rule: {current_rrule} | new rule: {self.rrule} | remaining: {len(self.calendar_event_ids)} | removed: {len(detached_events)}"
            _logger.info(log_msg)
            detached_events.unlink()