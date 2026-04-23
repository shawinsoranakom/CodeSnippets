def _compute_event_registrations_open(self):
        """ Compute whether people may take registrations for this event

          * for cancelled events, registrations are not open;
          * event.date_end -> if event is done, registrations are not open anymore;
          * event.start_sale_datetime -> lowest start date of tickets (if any; start_sale_datetime
            is False if no ticket are defined, see _compute_start_sale_date);
          * any ticket is available for sale (seats available) if any;
          * seats are unlimited or seats are available;
        """
        for event in self:
            event = event._set_tz_context()
            current_datetime = fields.Datetime.context_timestamp(event, fields.Datetime.now())
            date_end_tz = event.date_end.astimezone(pytz.timezone(event.date_tz or 'UTC')) if event.date_end else False
            event.event_registrations_open = event.kanban_state != 'cancel' and \
                event.event_registrations_started and \
                (date_end_tz >= current_datetime if date_end_tz else True) and \
                (not event.seats_limited or not event.seats_max or event.seats_available) and \
                (
                    # Not multi slots: open if no tickets or at least a sale available ticket
                    (not event.is_multi_slots and
                        (not event.event_ticket_ids or any(ticket.sale_available for ticket in event.event_ticket_ids)))
                    or
                    # Multi slots: open if at least a slot and no tickets or at least an ongoing ticket with availability
                    (event.is_multi_slots and event.event_slot_count and (
                        not event.event_ticket_ids or any(
                            ticket.is_launched and not ticket.is_expired and (
                                any(availability is None or availability > 0
                                    for availability in event._get_seats_availability([
                                        (slot, ticket)
                                        for slot in event.event_slot_ids
                                    ])
                                )
                            ) for ticket in event.event_ticket_ids
                        )
                    ))
                )