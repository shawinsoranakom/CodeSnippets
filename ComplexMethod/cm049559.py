def _compute_event_ticket_ids(self):
        """ Update event configuration from its event type. Depends are set only
        on event_type_id itself, not its sub fields. Purpose is to emulate an
        onchange: if event type is changed, update event configuration. Changing
        event type content itself should not trigger this method.

        When synchronizing tickets:

          * lines that have no registrations linked are remove;
          * type lines are added;

        Note that updating event_ticket_ids triggers _compute_start_sale_date
        (start_sale_datetime computation) so ensure result to avoid cache miss.
        """
        for event in self:
            if not event.event_type_id and not event.event_ticket_ids:
                event.event_ticket_ids = False
                continue

            # lines to keep: those with existing registrations
            tickets_to_remove = event.event_ticket_ids.filtered(lambda ticket: not ticket._origin.registration_ids)
            command = [Command.unlink(ticket.id) for ticket in tickets_to_remove]
            if event.event_type_id.event_type_ticket_ids:
                command += [
                    Command.create({
                        attribute_name: line[attribute_name] if not isinstance(line[attribute_name], models.BaseModel) else line[attribute_name].id
                        for attribute_name in self.env['event.type.ticket']._get_event_ticket_fields_whitelist()
                    }) for line in event.event_type_id.event_type_ticket_ids
                ]
            event.event_ticket_ids = command