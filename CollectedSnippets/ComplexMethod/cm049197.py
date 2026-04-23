def write(self, vals):
        values = vals
        recurrence_update_setting = values.get('recurrence_update')
        notify_context = self.env.context.get('dont_notify', False)

        # Forbid recurrence updates through Odoo and suggest user to update it in Outlook.
        if not notify_context:
            recurrency_in_batch = self.filtered(lambda ev: ev.recurrency)
            recurrence_update_attempt = recurrence_update_setting or 'recurrency' in values or recurrency_in_batch and len(recurrency_in_batch) > 0
            # Check if this is an Outlook recurring event with active sync
            if recurrence_update_attempt and 'active' not in values:
                recurring_events = self.filtered('microsoft_recurrence_master_id')
                if recurring_events and any(
                    event.with_user(organizer)._check_microsoft_sync_status()
                    for event in recurring_events
                    if (organizer := event._get_organizer())
                ):
                    self._forbid_recurrence_update()

        # When changing the organizer, check its sync status and verify if the user is listed as attendee.
        # Updates from Microsoft must skip this check since changing the organizer on their side is not possible.
        change_from_microsoft = self.env.context.get('dont_notify', False)
        deactivated_events_ids = []
        new_user_id = values.get('user_id')
        for event in self:
            if new_user_id and event.user_id.id != new_user_id and not change_from_microsoft and event.microsoft_id:
                sender_user, partner_ids = event._get_organizer_user_change_info(values)
                partner_included = sender_user.partner_id in event.attendee_ids.partner_id or sender_user.partner_id.id in partner_ids
                event._check_organizer_validation(sender_user, partner_included)
                if event.microsoft_id:
                    event._recreate_event_different_organizer(values, sender_user)
                    deactivated_events_ids.append(event.id)

        # check a Outlook limitation in overlapping the actual recurrence
        if recurrence_update_setting == 'self_only' and 'start' in values:
            self._check_recurrence_overlapping(values['start'])

        # if a single event becomes the base event of a recurrency, it should be first
        # removed from the Outlook calendar. Additionaly, checks if synchronization is not paused.
        if self.env.user._get_microsoft_sync_status() != "sync_paused" and values.get('recurrency'):
            for event in self:
                if not event.recurrency and not event.recurrence_id:
                    event._microsoft_delete(event._get_organizer(), event.microsoft_id, timeout=3)
                    event.microsoft_id = False
                    event.ms_universal_event_id = False

        deactivated_events = self.browse(deactivated_events_ids)
        # Update attendee status before 'values' variable is overridden in super.
        attendee_ids = values.get('attendee_ids')
        if attendee_ids and values.get('partner_ids'):
            (self - deactivated_events)._update_attendee_status(attendee_ids)

        res = super(CalendarEvent, (self - deactivated_events).with_context(dont_notify=notify_context)).write(values)

        # Deactivate events that were recreated after changing organizer.
        if deactivated_events:
            res |= super(CalendarEvent, deactivated_events.with_context(dont_notify=notify_context)).write({**values, 'active': False})

        if recurrence_update_setting in ('all_events',) and len(self) == 1 \
           and values.keys() & self._get_microsoft_synced_fields():
            self.recurrence_id.need_sync_m = True
        return res