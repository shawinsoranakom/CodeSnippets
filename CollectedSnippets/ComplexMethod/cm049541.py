def test_seats_slots_notickets(self):
        """ Test: slots, no tickets -> limits come from event itself """
        # self.test_event_slot_noticket.with_user(self.user_eventuser).write({'event_ticket_ids': [(5, 0)]})
        test_event = self.test_event_slot_noticket.with_user(self.user_eventregistrationdesk)
        first_slot = test_event.event_slot_ids.filtered(lambda s: s.start_hour == 9)
        second_slot = test_event.event_slot_ids.filtered(lambda s: s.start_hour == 13)

        Registration = self.env['event.registration'].with_user(self.user_eventregistrationdesk)

        # check ``_get_seats_availability`` tool, giving availabilities for slot / ticket combinations
        res = test_event._get_seats_availability([(first_slot, False), (second_slot, False)])
        self.assertEqual(res, [first_slot.seats_available, second_slot.seats_available])

        # check constraints at registration creation
        for create_input, should_crash in [
            # ok for event max seats for both slots
            (((first_slot, 2), (second_slot, 2)), False),
            # not enough seats on first slot
            (((first_slot, 3),), True),
            # not enough seats on second slot
            (((second_slot, 5),), True),
        ]:
            with self.subTest(create_input=create_input, should_crash=should_crash):
                create_values = []
                for slot, count in create_input:
                    create_values += [
                        {
                            'email': f'{slot.display_name}.{idx}@test.example.com',
                            'event_id': test_event.id,
                            'event_slot_id': slot.id,
                            'name': f'{slot.display_name} {idx}',
                        } for idx in range(count)
                    ]
                if should_crash:
                    with self.assertRaises(exceptions.ValidationError):
                        new = Registration.create(create_values)
                else:
                    new = Registration.create(create_values)
                    self.assertEqual(len(new), sum(count for _slot, count in create_input))
                    new.with_user(self.user_eventmanager).unlink()

        # check ``_verify_seats_availability`` itself
        for check_input, should_crash in [
            # ok for event max seats for both slots
            (((first_slot, False, 2), (second_slot, False, 4)), False),
            # not enough seats on first slot
            (((first_slot, False, 3),), True),
            # not enough seats on second slot
            (((second_slot, False, 5),), True),
        ]:
            with self.subTest(check_input=check_input, should_crash=should_crash):
                if should_crash:
                    with self.assertRaises(exceptions.ValidationError):
                        test_event._verify_seats_availability(check_input)
                else:
                    test_event._verify_seats_availability(check_input)

        # check constraint at write (active change) -> ok, check count
        all_slot2 = test_event.with_context(active_test=False).registration_ids.filtered(lambda r: r.event_slot_id == second_slot)
        self.assertEqual(len(all_slot2), 5, 'Test setup data: 3 active, 2 inactive')
        all_slot2.active = True
        self.assertEqual(second_slot.seats_available, 2)
        self.assertEqual(second_slot.seats_reserved, 3)

        # move them on first slot -> crash as it would be out of limits
        with self.assertRaises(exceptions.ValidationError):
            all_slot2.event_slot_id = first_slot.id