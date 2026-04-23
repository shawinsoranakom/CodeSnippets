def test_seats_slots_tickets(self):
        """ Test: slots and tickets -> limits come from event (global) and tickets """
        test_event = self.test_event.with_user(self.user_eventregistrationdesk)
        first_slot = test_event.event_slot_ids.filtered(lambda s: s.start_hour == 9)
        second_slot = test_event.event_slot_ids.filtered(lambda s: s.start_hour == 13)
        first_ticket = test_event.event_ticket_ids.filtered(lambda t: t.name == 'Classic')
        second_ticket = test_event.event_ticket_ids.filtered(lambda t: t.name == 'Better')
        third_ticket = test_event.event_ticket_ids.filtered(lambda t: t.name == 'VIP')

        Registration = self.env['event.registration'].with_user(self.user_eventregistrationdesk)

        # check ``_get_seats_availability`` tool, giving availabilities for slot / ticket combinations
        res = test_event._get_seats_availability([
            (first_slot, first_ticket), (first_slot, second_ticket), (first_slot, third_ticket),
            (second_slot, first_ticket), (second_slot, second_ticket), (second_slot, third_ticket),
        ])
        # first slot: 2 seats available, and VIP ticket has 1 seat anyway
        # second slot: 4 seats available, Better has 3 max and 1 taken and VIP 1 max
        self.assertEqual(res, [2, 2, 1, 4, 2, 1])

        # check constraints at registration creation
        for create_input, should_crash in [
            (((first_slot, second_ticket, 2),), False),
            # not enough seats for first slot
            (((first_slot, first_ticket, 5),), True),
            # not enough seats on VIP ticket
            (((second_slot, third_ticket, 2),), True),
        ]:
            with self.subTest(create_input=create_input, should_crash=should_crash):
                create_values = []
                for slot, ticket, count in create_input:
                    create_values += [
                        {
                            'email': f'{slot.display_name}.{ticket.name}.{idx}@test.example.com',
                            'event_id': test_event.id,
                            'event_slot_id': slot.id,
                            'event_ticket_id': ticket.id,
                            'name': f'{slot.display_name} {ticket.name} {idx}',
                        } for idx in range(count)
                    ]
                if should_crash:
                    with self.assertRaises(exceptions.ValidationError):
                        new = Registration.create(create_values)
                else:
                    new = Registration.create(create_values)
                    self.assertEqual(len(new), sum(count for _slot, _ticket, count in create_input))
                    new.with_user(self.user_eventmanager).unlink()

        # check create constraint through embed 2many: 2 VIPs is not possible
        with self.assertRaises(exceptions.ValidationError):
            test_event.with_user(self.user_eventmanager).write({
                'registration_ids': [
                    (0, 0, {'event_slot_id': second_slot.id, 'event_ticket_id': third_ticket.id}),
                    (0, 0, {'event_slot_id': second_slot.id, 'event_ticket_id': third_ticket.id}),
                ],
            })
        # one of them is archived, ok for limit
        test_event.with_user(self.user_eventmanager).write({
            'registration_ids': [
                (0, 0, {'event_slot_id': second_slot.id, 'event_ticket_id': third_ticket.id, 'active': False}),
                (0, 0, {'event_slot_id': second_slot.id, 'event_ticket_id': third_ticket.id}),
            ],
        })
        archived_vip = test_event.with_context(active_test=False).registration_ids.filtered(lambda r: r.event_slot_id == second_slot and r.event_ticket_id == third_ticket and not r.active)
        self.assertTrue(archived_vip)
        # writing on active triggers constraint on VIP
        with self.assertRaises(exceptions.ValidationError):
            archived_vip.active = True