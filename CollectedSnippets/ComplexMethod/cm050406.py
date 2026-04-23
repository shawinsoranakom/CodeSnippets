def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for convert in self:
            # setting user as void should not trigger a new team computation
            if not convert.user_id and not convert.user_ids and convert.team_id:
                continue
            user = convert.user_id or convert.user_ids and convert.user_ids[0] or self.env.user
            if convert.team_id and user in convert.team_id.member_ids | convert.team_id.user_id:
                continue
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=None)
            convert.team_id = team.id