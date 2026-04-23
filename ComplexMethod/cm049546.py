def execute(self):
        now = fields.Datetime.now()
        for scheduler in self._filter_template_ref():
            if scheduler.interval_type == 'after_sub':
                scheduler._execute_attendee_based()
            elif scheduler.event_id.is_multi_slots:
                scheduler._execute_slot_based()
            else:
                # before or after event -> one shot communication, once done skip
                if scheduler.mail_done:
                    continue
                # do not send emails if the mailing was scheduled before the event but the event is over
                if scheduler.scheduled_date <= now and (scheduler.interval_type not in ('before_event', 'after_event_start') or scheduler.event_id.date_end > now):
                    scheduler._execute_event_based()
            scheduler.error_datetime = False
        return True