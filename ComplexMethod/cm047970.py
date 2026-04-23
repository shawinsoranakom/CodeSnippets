def _compute_user_in_teams_ids(self):
        """ Give users not to add in the currently chosen team to avoid duplicates.
        In multi membership mode this field is empty as duplicates are allowed. """
        if all(m.is_membership_multi for m in self):
            member_user_ids = self.env['res.users']
        elif self.ids:
            member_user_ids = self.env['crm.team.member'].search([('id', 'not in', self.ids)]).user_id
        else:
            member_user_ids = self.env['crm.team.member'].search([]).user_id
        for member in self:
            if member_user_ids:
                member.user_in_teams_ids = member_user_ids
            elif member.crm_team_id:
                member.user_in_teams_ids = member.crm_team_id.member_ids
            elif self.env.context.get('default_crm_team_id'):
                member.user_in_teams_ids = self.env['crm.team'].browse(self.env.context['default_crm_team_id']).member_ids
            else:
                member.user_in_teams_ids = self.env['res.users']