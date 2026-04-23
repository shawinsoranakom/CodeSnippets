def _verify_updated_quantity(
        self, order_line, product_id, new_qty, uom_id, *, event_slot_id=False, event_ticket_id=False, **kwargs
    ):
        """Restrict quantity updates for event tickets according to available seats."""
        new_qty, warning = super()._verify_updated_quantity(
            order_line,
            product_id,
            new_qty,
            uom_id,
            event_slot_id=event_slot_id,
            event_ticket_id=event_ticket_id,
            **kwargs,
        )

        if not event_ticket_id:
            if not order_line.event_ticket_id or new_qty < order_line.product_uom_qty:
                return new_qty, warning
            else:
                return order_line.product_uom_qty, _("You cannot raise manually the event ticket quantity in your cart")

        # Adding new ticket to the cart (might be automatically linked to an existing line)
        ticket = self.env['event.event.ticket'].browse(event_ticket_id).exists()
        if not ticket:
            raise UserError(_("The provided ticket doesn't exist"))
        slot = self.env['event.slot'].browse(event_slot_id).exists()
        if event_slot_id and not slot:
            raise UserError(_("The provided ticket slot doesn't exist"))

        # TODO TDE consider full cart qty and not only added qty
        # if event seats are not auto confirmed.
        # Since created registrations are automatically reserved
        # We should only consider new added qty and not full quantity
        # when checking for seat availability
        existing_qty = order_line.product_uom_qty if order_line else 0
        qty_added = new_qty - existing_qty
        warning = ''
        ticket_seats_available = ticket.event_id._get_seats_availability([(slot, ticket)])[0] if slot else ticket.seats_available
        if ticket.seats_limited and ticket_seats_available <= 0:
            # Remove existing line if exists and do not add a new one
            # if no ticket is available anymore
            new_qty = existing_qty
            warning = _(
                'Sorry, The %(ticket)s tickets for the %(event)s event are sold out.',
                ticket=ticket.name,
                event=ticket.event_id.name,
            )
        elif ticket.seats_limited and qty_added > ticket_seats_available:
            new_qty = existing_qty + ticket_seats_available
            warning = _(
                'Sorry, only %(remaining_seats)d seats are still available for the %(ticket)s ticket for the %(event)s event%(slot)s.',
                remaining_seats=ticket_seats_available,
                slot=f' on {slot.name}' if slot else '',
                ticket=ticket.name,
                event=ticket.event_id.name,
            )

        return new_qty, warning