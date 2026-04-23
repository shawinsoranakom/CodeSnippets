def _create_registrations_for_slot_and_ticket(cls, event, slot, ticket, count, **add_values):
        return cls.env['event.registration'].create([
            dict(
                    {
                    'email': f'{slot.id if slot else "NoSlot"}.{ticket.id if ticket else "NoTicket"}@test.example.com',
                    'event_id': event.id,
                    'event_slot_id': slot.id if slot else False,
                    'event_ticket_id': ticket.id if ticket else False,
                    'name': f'{slot.id if slot else "NoSlot"}.{ticket.id if ticket else "NoTicket"}',
                }, **add_values
            ) for idx in range(0, count)
        ])