def _handle_allday_recurrences_edge_case(self, records, vals_list):
        """
        When creating 'All Day' recurrent event, the first event is wrongly synchronized as
        a single event and then its recurrence creates a duplicated event. We must manually
        set the 'need_sync' attribute as False in order to avoid this unwanted behavior.
        """
        if vals_list and self._name == 'calendar.event':
            forbid_sync = all(not vals.get('need_sync', True) for vals in vals_list)
            records_to_skip = records.filtered(lambda r: r.need_sync and r.allday and r.recurrency and not r.recurrence_id)
            if forbid_sync and records_to_skip:
                records_to_skip.with_context(send_updates=False).need_sync = False