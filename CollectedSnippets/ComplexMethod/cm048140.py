def create(self, vals_list):
        # Prevent sending update notification when _inverse_dates is called
        self = self.with_context(is_calendar_event_new=True)
        defaults = self.browse().default_get([
            'activity_ids', 'allday', 'description', 'name', 'partner_ids',
            'res_model_id', 'res_id', 'start', 'user_id',
        ])

        vals_list = [  # Else bug with quick_create when we are filter on an other user
            {
                **vals,
                'activity_ids': vals.get('activity_ids', defaults.get('activity_ids')),
                'allday': vals.get('allday', defaults.get('allday')),
                'description': vals.get('description', defaults.get('description')),
                'name': vals.get('name', defaults.get('name')),
                # when res_id is not defined or vals['res_id'] == 0, fallback on default
                'res_id': vals.get('res_id') or defaults.get('res_id'),
                'res_model': vals.get('res_model', defaults.get('res_model')),
                'res_model_id': vals.get('res_model_id', defaults.get('res_model_id')),
                'start': vals.get('start', defaults.get('start')),
                'user_id': vals.get('user_id', defaults.get('user_id', self.env.user.id)),
             } for vals in vals_list
        ]
        meeting_activity_types = self.env['mail.activity.type'].search([('category', '=', 'meeting')])
        # get list of models ids and filter out None values directly
        model_ids = list(filter(None, {values['res_model_id'] for values in vals_list}))
        all_models = self.env['ir.model'].sudo().browse(model_ids)
        # TDE FIXME: clean that method, be more values-based
        excluded_models = self._get_activity_excluded_models()

        # if user is creating an event for an activity that already has one, create a second activity
        existing_event, existing_type = self.browse(), self.env['mail.activity.type']
        orig_activity_ids = self.env['mail.activity'].browse(self.env.context.get('orig_activity_ids', []))

        if len(orig_activity_ids) == 1:
            existing_event = orig_activity_ids.calendar_event_id
            if existing_event and orig_activity_ids.activity_type_id.category == 'meeting':
                existing_type = orig_activity_ids.activity_type_id

        if meeting_activity_types:
            for values in vals_list:
                # created from calendar: try to create an activity on the related record
                if values['activity_ids'] and not existing_event:
                    continue
                res_model = all_models.filtered(lambda m: m.id == values['res_model_id'])
                res_id = values['res_id']
                if not res_model or not res_id or res_model.model in excluded_models or not res_model.is_mail_activity:
                    continue

                meeting_activity_type = self.env['mail.activity.type']
                if existing_type and existing_type.res_model in {False, res_model.model}:
                    meeting_activity_type = existing_type
                if not meeting_activity_type:
                    meeting_activity_type = meeting_activity_types.filtered(
                        lambda act: act.res_model in {False, res_model.model}
                    )
                if not meeting_activity_type:
                    continue

                activity_vals = {
                    'res_model_id': values['res_model_id'],
                    'res_id': res_id,
                    'activity_type_id': meeting_activity_type[0].id,
                }
                if values['description']:
                    activity_vals['note'] = values['description']
                if values['name']:
                    activity_vals['summary'] = values['name']
                if values['start']:
                    activity_vals['date_deadline'] = self._get_activity_deadline_from_start(fields.Datetime.from_string(values['start']), values['allday'])
                if values['user_id']:
                    activity_vals['user_id'] = values['user_id']
                values['activity_ids'] = [(0, 0, activity_vals)]

        self._set_videocall_location(vals_list)

        # Add commands to create attendees from partners (if present) if no attendee command
        # is already given (coming from Google event for example).
        # Automatically add the current partner when creating an event if there is none (happens when we quickcreate an event)
        default_partners_ids = defaults.get('partner_ids') or ([(4, self.env.user.partner_id.id)])
        vals_list = [
            dict(vals, attendee_ids=self._attendees_values(vals.get('partner_ids', default_partners_ids)))
            if not vals.get('attendee_ids')
            else vals
            for vals in vals_list
        ]

        if not self.env.context.get('skip_contact_description'):
            # Add organizer and first partner details to event description
            organizer_ids, partner_ids = set(), set()
            vals_partner_list = []
            for vals in vals_list:
                if vals.get('user_id'):
                    organizer_ids.add(vals['user_id'])
                # attendee_ids structure = [[2, partner_id_to_remove], [0, 0, {'partner_id': partner_id_to_add}], ...]
                partner_ids_from_attendees = {
                    attendee_vals[2]['partner_id']
                    for attendee_vals in vals['attendee_ids']
                    if len(attendee_vals) > 2 and isinstance(attendee_vals[2], dict) and 'partner_id' in attendee_vals[2]
                }
                partner_ids.update(partner_ids_from_attendees)
                vals_partner_list.append(partner_ids_from_attendees)
            organizers = self.env['res.users'].browse(organizer_ids).with_prefetch(organizer_ids)
            partners = self.env['res.partner'].browse(partner_ids).with_prefetch(partner_ids)

            for vals, vals_partner_ids in zip(vals_list, vals_partner_list):
                contact_description = self._get_contact_details_description(
                    organizers.browse(vals.get('user_id', False)),
                    partners.browse(vals_partner_ids),
                )
                if not is_html_empty(contact_description):
                    base_description = f"{vals['description']}<br/>" if not is_html_empty(vals.get('description')) else ''
                    vals['description'] = f'<div>{base_description}{contact_description}</div>'

        recurrence_fields = self._get_recurrent_fields()
        recurring_vals = [vals for vals in vals_list if vals.get('recurrency')]
        other_vals = [vals for vals in vals_list if not vals.get('recurrency')]
        events = super().create(other_vals)

        for vals in recurring_vals:
            vals['follow_recurrence'] = True
        recurring_events = super().create(recurring_vals)
        events += recurring_events

        for event, vals in zip(recurring_events, recurring_vals):
            recurrence_values = {field: vals.pop(field) for field in recurrence_fields if field in vals}
            if vals.get('recurrency'):
                detached_events = event.with_context(skip_contact_description=True)._apply_recurrence_values(recurrence_values)
                detached_events.active = False

        events.filtered(lambda event: event.start > fields.Datetime.now()).attendee_ids._send_invitation_emails()

        # update activities based on calendar event data, unless already prepared
        # above manually. Heuristic: a new command (0, 0, vals) is considered as
        # complete
        to_sync_activities = self.browse()
        for event, event_values in zip(events, vals_list):
            if any(command[0] != 0 for command in event_values.get('activity_ids') or []):
                to_sync_activities += event
        to_sync_activities._sync_activities(fields={f for vals in vals_list for f in vals})

        if not self.env.context.get('dont_notify'):
            alarm_events = self.env['calendar.event']
            for event, values in zip(events, vals_list):
                if values.get('allday'):
                    # All day events will trigger the _inverse_date method which will create the trigger.
                    continue
                alarm_events |= event
            recurring_events = alarm_events.filtered('recurrence_id')
            recurring_events.recurrence_id._setup_alarms()
            (alarm_events - recurring_events)._setup_alarms()
        return events.with_context(is_calendar_event_new=False)