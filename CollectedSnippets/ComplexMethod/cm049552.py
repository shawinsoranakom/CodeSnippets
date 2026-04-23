def _compute_seats(self):
        # initialize fields to 0
        for slot in self:
            slot.seats_reserved = slot.seats_used = slot.seats_available = 0
        # aggregate registrations by slot and by state
        state_field = {
            'open': 'seats_reserved',
            'done': 'seats_used',
        }
        base_vals = dict.fromkeys(state_field.values(), 0)
        results = {slot_id: dict(base_vals) for slot_id in self.ids}
        if self.ids:
            query = """ SELECT event_slot_id, state, count(event_slot_id)
                        FROM event_registration
                        WHERE event_slot_id IN %s AND state IN ('open', 'done') AND active = true
                        GROUP BY event_slot_id, state
                    """
            self.env['event.registration'].flush_model(['event_slot_id', 'state', 'active'])
            self.env.cr.execute(query, (tuple(self.ids),))
            res = self.env.cr.fetchall()
            for slot_id, state, num in res:
                results[slot_id][state_field[state]] = num
        # compute seats_available
        for slot in self:
            slot.update(results.get(slot._origin.id or slot.id, base_vals))
            if slot.event_id.seats_max > 0:
                slot.seats_available = slot.event_id.seats_max - (slot.seats_reserved + slot.seats_used)
            slot.seats_taken = slot.seats_reserved + slot.seats_used