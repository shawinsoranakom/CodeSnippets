def _sync_recurrence_microsoft2odoo(self, microsoft_events, new_events=None):
        recurrent_masters = new_events.filter(lambda e: e.is_recurrence()) if new_events else []
        recurrents = new_events.filter(lambda e: e.is_recurrent_not_master()) if new_events else []
        default_values = {'need_sync_m': False}

        new_recurrence = self.env['calendar.recurrence']
        updated_events = self.env['calendar.event']

        # --- create new recurrences and associated events ---
        for recurrent_master in recurrent_masters:
            new_calendar_recurrence = dict(
                self.env['calendar.recurrence']._microsoft_to_odoo_values(recurrent_master, default_values, with_ids=True),
                need_sync_m=False
            )
            to_create = recurrents.filter(
                lambda e: e.seriesMasterId == new_calendar_recurrence['microsoft_id']
            )
            recurrents -= to_create
            base_values = dict(
                self.env['calendar.event']._microsoft_to_odoo_values(recurrent_master, default_values, with_ids=True),
                need_sync_m=False
            )
            to_create_values = []
            if new_calendar_recurrence.get('end_type', False) in ['count', 'forever']:
                to_create = list(to_create)[:MAX_RECURRENT_EVENT]
            for recurrent_event in to_create:
                if recurrent_event.type == 'occurrence':
                    value = self.env['calendar.event']._microsoft_to_odoo_recurrence_values(recurrent_event, base_values)
                else:
                    value = self.env['calendar.event']._microsoft_to_odoo_values(recurrent_event, default_values)

                to_create_values += [dict(value, need_sync_m=False)]

            new_calendar_recurrence['calendar_event_ids'] = [(0, 0, to_create_value) for to_create_value in to_create_values]
            new_recurrence_odoo = self.env['calendar.recurrence'].with_context(dont_notify=True).create(new_calendar_recurrence)
            new_recurrence_odoo.base_event_id = new_recurrence_odoo.calendar_event_ids[0] if new_recurrence_odoo.calendar_event_ids else False
            new_recurrence |= new_recurrence_odoo

        # --- update events in existing recurrences ---
        # Important note:
        # To map existing recurrences with events to update, we must use the universal id
        # (also known as ICalUId in the Microsoft API), as 'seriesMasterId' attribute of events
        # is specific to the Microsoft user calendar.
        ms_recurrence_ids = list({x.seriesMasterId for x in recurrents})
        ms_recurrence_uids = {r.id: r.iCalUId for r in microsoft_events if r.id in ms_recurrence_ids}
        recurrences = self.env['calendar.recurrence'].search([('ms_universal_event_id', 'in', microsoft_events.uids)])
        for recurrent_master_id in ms_recurrence_ids:
            recurrence_id = recurrences.filtered(
                lambda ev: ev.ms_universal_event_id == ms_recurrence_uids[recurrent_master_id]
            )
            to_update = recurrents.filter(lambda e: e.seriesMasterId == recurrent_master_id)
            for recurrent_event in to_update:
                if recurrent_event.type == 'occurrence':
                    value = self.env['calendar.event']._microsoft_to_odoo_recurrence_values(
                        recurrent_event, {'need_sync_m': False}
                    )
                else:
                    value = self.env['calendar.event']._microsoft_to_odoo_values(recurrent_event, default_values)
                existing_event = recurrence_id.calendar_event_ids.filtered(
                    lambda e: e._is_matching_timeslot(value['start'], value['stop'], recurrent_event.isAllDay)
                )
                if not existing_event:
                    continue
                value.pop('start')
                value.pop('stop')
                existing_event._write_from_microsoft(recurrent_event, value)
                updated_events |= existing_event
            new_recurrence |= recurrence_id
        return new_recurrence, updated_events