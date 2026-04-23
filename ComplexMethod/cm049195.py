def create(self, vals_list):
        notify_context = self.env.context.get('dont_notify', False)

        # Forbid recurrence creation in Odoo, suggest its creation in Outlook due to the spam limitation.
        recurrency_in_batch = any(vals.get('recurrency') for vals in vals_list)
        if self._check_microsoft_sync_status() and not notify_context and recurrency_in_batch:
            self._forbid_recurrence_creation()

        vals_check_organizer = self._check_organizer_validation_conditions(vals_list)
        for vals in [vals for vals, check_organizer in zip(vals_list, vals_check_organizer) if check_organizer]:
            # If event has a different organizer, check its sync status and verify if the user is listed as attendee.
            sender_user, partner_ids = self._get_organizer_user_change_info(vals)
            partner_included = partner_ids and len(partner_ids) > 0 and sender_user.partner_id.id in partner_ids
            self._check_organizer_validation(sender_user, partner_included)

        # for a recurrent event, we do not create events separately but we directly
        # create the recurrency from the corresponding calendar.recurrence.
        # That's why, events from a recurrency have their `need_sync_m` attribute set to False.
        return super(CalendarEvent, self.with_context(dont_notify=notify_context)).create([
            dict(vals, need_sync_m=False) if vals.get('recurrence_id') or vals.get('recurrency') else vals
            for vals in vals_list
        ])