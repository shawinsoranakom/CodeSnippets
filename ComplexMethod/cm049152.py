def website_form_input_filter(self, request, values):
        values['medium_id'] = values.get('medium_id') or \
                              self.sudo().default_get(['medium_id']).get('medium_id') or \
                              self.env['utm.medium']._fetch_or_create_utm_medium('website').id
        values['team_id'] = values.get('team_id') or \
                            request.website.crm_default_team_id.id
        values['user_id'] = values.get('user_id') or \
                            request.website.crm_default_user_id.id
        if not values['user_id'] and values['team_id'] and not self._is_rule_based_assignment_activated():
            values['user_id'] = self.env['crm.team'].sudo().browse([values['team_id']]).user_id.id
        if values.get('team_id'):
            values['type'] = 'lead' if self.env['crm.team'].sudo().browse(values['team_id']).use_leads else 'opportunity'
        else:
            values['type'] = 'lead' if self.env.user.has_group('crm.group_use_lead') else 'opportunity'

        return values