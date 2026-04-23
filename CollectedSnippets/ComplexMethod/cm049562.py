def _verify_seats_availability(self, slot_tickets):
        """ Check event seats availability, for combinations of slot / ticket.

        :param slot_tickets: a list of tuples(slot, ticket, count). Slot and
          ticket are optional, depending on event configuration. If count is 0
          it is a simple check current values do not overflow limit. If count
          is given, it serves as a check there are enough remaining seats.
        :raises ValidationError: if the event / slot / ticket do not have
          enough available seats
        """
        self.ensure_one()
        if not (all(len(item) == 3 for item in slot_tickets)):
            raise ValueError('Input should be a list of tuples containing slot, ticket, count')

        sold_out = []
        availabilities = self._get_seats_availability([(item[0], item[1]) for item in slot_tickets])
        for (slot, ticket, count), available in zip(slot_tickets, availabilities, strict=True):
            if available is None:  # unconstrained
                continue
            if available < count:
                if slot and ticket:
                    name = f'{ticket.name} - {slot.display_name}'
                elif slot:
                    name = slot.display_name
                elif ticket:
                    name = ticket.name
                else:
                    name = self.name
                sold_out.append((name, count - available))

        if sold_out:
            info = []  # note: somehow using list comprehension make translate.py crash in default lang
            for item in sold_out:
                info.append(_('%(slot_name)s: missing %(count)s seat(s)', slot_name=item[0], count=item[1]))
            raise ValidationError(
                _('There are not enough seats available for %(event_name)s:\n%(sold_out_info)s',
                  event_name=self.name,
                  sold_out_info='\n'.join(info),
                )
            )