def _execute_slot_based(self):
        """ Main scheduler method when running in slot-based mode aka
        'after_event' or 'before_event' (and their negative counterparts) on
        events with slots. This is a global communication done once i.e. we do
        not track each registration individually. """
        # create slot-specific schedulers if not existing
        missing_slots = self.event_id.event_slot_ids - self.mail_slot_ids.event_slot_id
        if missing_slots:
            self.write({'mail_slot_ids': [
                (0, 0, {'event_slot_id': slot.id})
                for slot in missing_slots
            ]})

        # filter slots to contact
        now = fields.Datetime.now()
        for mail_slot in self.mail_slot_ids:
            # before or after event -> one shot communication, once done skip
            if mail_slot.mail_done:
                continue
            # do not send emails if the mailing was scheduled before the slot but the slot is over
            if mail_slot.scheduled_date <= now and (self.interval_type not in ('before_event', 'after_event_start') or mail_slot.event_slot_id.end_datetime > now):
                self._execute_event_based(mail_slot=mail_slot)