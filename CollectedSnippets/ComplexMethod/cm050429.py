def _merge_get_fields_specific(self):
        return {
            'description': lambda fname, leads: '<br/><br/>'.join(desc for desc in leads.mapped('description') if not is_html_empty(desc)),
            'type': lambda fname, leads: 'opportunity' if any(lead.type == 'opportunity' for lead in leads) else 'lead',
            'priority': lambda fname, leads: max(priorities) if (priorities := leads.filtered('priority').mapped('priority')) else False,
            'tag_ids': lambda fname, leads: leads.mapped('tag_ids'),
            'lost_reason_id': lambda fname, leads:
                False if leads and leads[0].probability
                else next((lead.lost_reason_id for lead in leads if lead.lost_reason_id), False),
        }