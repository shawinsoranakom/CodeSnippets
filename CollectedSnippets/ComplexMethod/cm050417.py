def _compute_meeting_display(self):
        now = fields.Datetime.now()
        meeting_data = self.env['calendar.event'].sudo()._read_group([
            ('opportunity_id', 'in', self.ids),
        ], ['opportunity_id'], ['start:array_agg', 'start:max'])
        mapped_data = {
            lead: {
                'last_meeting_date': last_meeting_date,
                'next_meeting_date': min([dt for dt in meeting_start_dates if dt > now] or [False]),
            } for lead, meeting_start_dates, last_meeting_date in meeting_data
        }
        for lead in self:
            lead_meeting_info = mapped_data.get(lead)
            if not lead_meeting_info:
                lead.meeting_display_date = False
                lead.meeting_display_label = _('No Meeting')
            elif lead_meeting_info['next_meeting_date']:
                lead.meeting_display_date = fields.Datetime.context_timestamp(lead, lead_meeting_info['next_meeting_date'])
                lead.meeting_display_label = _('Next Meeting')
            else:
                lead.meeting_display_date = fields.Datetime.context_timestamp(lead, lead_meeting_info['last_meeting_date'])
                lead.meeting_display_label = _('Last Meeting')