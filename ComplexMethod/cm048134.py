def test_attendees_state_after_update(self):
        """ Ensure that after the organizer updates a recurrence, the attendees state will be pending and current user accepted. """
        # Create events with organizer and attendee state set as accepted.
        organizer = self.env.ref('base.user_admin')
        attendee_partner = self.env['res.partner'].create({'name': "attendee", "email": 'attendee@email.com'})
        first_event = self.env['calendar.event'].with_user(organizer).create({
            'name': "Recurrence",
            'start': datetime(2023, 10, 18, 8, 0),
            'stop': datetime(2023, 10, 18, 10, 0),
            'rrule': u'FREQ=WEEKLY;COUNT=5;BYDAY=WE',
            'recurrency': True,
            'partner_ids': [(4, organizer.partner_id.id), (4, attendee_partner.id)],
        })
        recurrence_id = first_event.recurrence_id.id

        # Accept all events for all attendees and ensure their acceptance.
        for event in first_event.recurrence_id.calendar_event_ids:
            for attendee in event.attendee_ids:
                attendee.state = 'accepted'

        # Change time fields of the recurrence by organizer in "all_events" mode. Events must reset attendee status to 'needsAction'.
        first_event.with_user(organizer).write({
            'start': first_event.start + relativedelta(hours=2),
            'stop': first_event.stop + relativedelta(hours=2),
            'recurrence_update': 'all_events',
        })
        first_event = self.env['calendar.recurrence'].search([('id', '>', recurrence_id)]).base_event_id
        recurrence_id = first_event.recurrence_id.id

        # Ensure that attendee status is pending after organizer (current user) update time values.
        for event in first_event.recurrence_id.calendar_event_ids:
            for attendee in event.attendee_ids:
                if attendee.partner_id == organizer.partner_id:
                    self.assertEqual(attendee.state, "accepted", "Organizer must remain accepted after time values update.")
                else:
                    self.assertEqual(attendee.state, "needsAction", "Attendees state except organizer must be pending after update.")

        # Accept all events again for all attendes.
        for event in first_event.recurrence_id.calendar_event_ids:
            for attendee in event.attendee_ids:
                attendee.state = 'accepted'

        # Change time fields of the recurrence by organizer in "future_events" mode. Events must reset attendee status to 'needsAction'.
        second_event = first_event.recurrence_id.calendar_event_ids.sorted('start')[1]
        second_event.with_user(organizer).write({
            'start': second_event.start + relativedelta(hours=2),
            'stop': second_event.stop + relativedelta(hours=2),
            'recurrence_update': 'future_events',
        })
        second_event = self.env['calendar.recurrence'].search([('id', '>', recurrence_id)]).base_event_id

        # Ensure that first event is accepted for everyone and also from the second event on, the state in pending for attendees except organizer.
        self.assertTrue(first_event.active, "Event from previous recurrence must remain active after the second event got updated.")
        self.assertTrue(all(attendee.state == 'accepted' for attendee in first_event.attendee_ids), "Attendees state from previous event must remain accepted.")
        for event in second_event.recurrence_id.calendar_event_ids:
            for attendee in event.attendee_ids:
                if attendee.partner_id == organizer.partner_id:
                    self.assertEqual(attendee.state, "accepted", "Current user must remain accepted after time values update.")
                else:
                    self.assertEqual(attendee.state, "needsAction", "Attendees state except current user must be pending after update.")