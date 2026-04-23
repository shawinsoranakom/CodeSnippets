def _process_step_create_lead_and_forward(self, discuss_channel):
        lead = self._process_step_create_lead(discuss_channel)
        teams = lead.team_id
        if not teams:
            possible_teams = self.env["crm.team"].search(
                Domain("assignment_optout", "=", False) & (
                    Domain("use_leads", "=", True) | Domain("use_opportunities", "=", True)
                ),
            )
            teams = possible_teams.filtered(
                lambda team: team.assignment_max
                and lead.filtered_domain(literal_eval(team.assignment_domain or "[]"))
            )
        if self.env.user.partner_id.company_id:
            teams = teams.filtered(
                lambda team: not team.company_id
                or team.company_id == self.env.user.partner_id.company_id
            )
        assignable_user_ids = [
            member.user_id.id
            for member in teams.crm_team_member_ids
            if not member.assignment_optout
            and member._get_assignment_quota() > 0
            and lead.filtered_domain(literal_eval(member.assignment_domain or "[]"))
        ]
        previous_operator = discuss_channel.livechat_operator_id
        users = self.env["res.users"]
        if discuss_channel.livechat_channel_id:
            # sudo: im_livechat.channel - getting available operators is acceptable
            users = discuss_channel.livechat_channel_id.sudo()._get_available_operators_by_livechat_channel(
                self.env["res.users"].browse(assignable_user_ids)
            )[discuss_channel.livechat_channel_id]
        message = discuss_channel._forward_human_operator(self, users=users)
        if previous_operator != discuss_channel.livechat_operator_id:
            user = next(user for user in users if user.partner_id == discuss_channel.livechat_operator_id)
            lead.user_id = user
            lead.team_id = next(team for team in teams if user in team.crm_team_member_ids.user_id)
            msg = self.env._("Created a new lead: %s", lead._get_html_link())
            user._bus_send_transient_message(discuss_channel, msg)
            # Call flush_recordset() now (as sudo), otherwise flush_all() is called at the end of
            # the request with a non-sudo env, which fails (as public user) to compute some crm.lead
            # fields having dependencies on assigned user_id.
            lead.flush_recordset()
        return message