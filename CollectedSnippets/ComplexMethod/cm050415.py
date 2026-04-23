def _assign_and_convert_leads(self, force_quota=False):
        """ Main processing method to assign leads to sales team members. It also
        converts them into opportunities. This method should be called after
        ``_allocate_leads`` as this method assigns leads already allocated to
        the member's team. Its main purpose is therefore to distribute team
        workload on its members based on their capacity.

        This method follows the following heuristic
            * Get quota per member
            * Find all leads to be assigned per team
            * Sort list of members per number of leads received in the last 24h
            * Assign the lead using round robin
                * Find the first member with a compatible domain
                * Assign the lead
                * Move the member at the end of the list if quota is not reached
                * Remove it otherwise
                * Move to the next lead

        :param bool force_quota: see ``CrmTeam._action_assign_leads()``;

        :returns: dict() with each member assignment result:
          membership: {
            'assigned': set of lead IDs directly assigned to the member;
          }, ...

        """
        auto_commit = not modules.module.current_test
        result_data = {}
        commit_bundle_size = int(self.env['ir.config_parameter'].sudo().get_param('crm.assignment.commit.bundle', 100))
        teams_with_members = self.filtered(lambda team: team.crm_team_member_ids)
        quota_per_member = {member: member._get_assignment_quota(force_quota=force_quota) for member in self.crm_team_member_ids}
        counter = 0
        leads_per_team = dict(self.env['crm.lead']._read_group(
            teams_with_members._get_lead_to_assign_domain(),
            ['team_id'],
            # Do not use recordset aggregation to avoid fetching all the leads at once in memory
            # We want to have in memory only leads for the current team
            # and make sure we need them before fetching them
            ['id:array_agg'],
        ))

        def _assign_lead(lead, members, member_leads, members_quota, assign_lst, optional_lst=None):
            """ Find relevant member whose domain(s) accept the lead. If found convert
            and update internal structures accordingly. """
            member_found = next((member for member in members if lead in member_leads[member]), False)
            if not member_found:
                return
            lead.with_context(mail_auto_subscribe_no_notify=True).convert_opportunity(
                lead.partner_id,
                user_ids=member_found.user_id.ids
            )
            result_data[member_found]['assigned'] += lead

            # if member still has quota, move at end of list; otherwise just remove
            assign_lst.remove(member_found)
            if optional_lst is not None:
                optional_lst.remove(member_found)
            members_quota[member_found] -= 1
            if members_quota[member_found] > 0:
                assign_lst.append(member_found)
                if optional_lst is not None:
                    optional_lst.append(member_found)
            return member_found

        for team, leads_to_assign_ids in leads_per_team.items():
            members_to_assign = list(team.crm_team_member_ids.filtered(lambda member:
                not member.assignment_optout and quota_per_member.get(member, 0) > 0
            ).sorted(key=lambda member: quota_per_member.get(member, 0), reverse=True))
            if not members_to_assign:
                continue
            result_data.update({
                member: {"assigned": self.env["crm.lead"], "quota": quota_per_member[member]}
                for member in members_to_assign
            })
            # Need to check that record still exists since the ids have been fetched at the beginning of the process
            # Previous iteration has committed the change, records may have been deleted in the meanwhile
            to_assign = self.env['crm.lead'].browse(leads_to_assign_ids).exists()

            members_to_assign_wpref = [
                m for m in members_to_assign
                if m.assignment_domain_preferred and literal_eval(m.assignment_domain_preferred or '')
            ]
            preferred_leads_per_member = {
                member: to_assign.filtered_domain(
                    Domain.AND([
                        literal_eval(member.assignment_domain or '[]'),
                        literal_eval(member.assignment_domain_preferred)
                    ])
                ) for member in members_to_assign_wpref
            }
            preferred_leads = self.env['crm.lead'].concat(*[lead for lead in preferred_leads_per_member.values()])
            assigned_preferred_leads = self.env['crm.lead']

            # first assign loop: preferred leads, always priority
            for lead in preferred_leads.sorted(lambda lead: (-lead.probability, id)):
                counter += 1
                member_found = _assign_lead(lead, members_to_assign_wpref, preferred_leads_per_member, quota_per_member, members_to_assign, members_to_assign_wpref)
                if not member_found:
                    continue
                assigned_preferred_leads += lead
                if auto_commit and counter % commit_bundle_size == 0:
                    self.env.cr.commit()

            # second assign loop: fill up with other leads
            to_assign = to_assign - assigned_preferred_leads
            leads_per_member = {
                member: to_assign.filtered_domain(literal_eval(member.assignment_domain or '[]'))
                for member in members_to_assign
            }
            for lead in to_assign.sorted(lambda lead: (-lead.probability, id)):
                counter += 1
                member_found = _assign_lead(lead, members_to_assign, leads_per_member, quota_per_member, members_to_assign)
                if not member_found:
                    continue
                if auto_commit and counter % commit_bundle_size == 0:
                    self.env.cr.commit()

            # Make sure we commit at least at the end of the team
            if auto_commit:
                self.env.cr.commit()
            # Once we are done with a team we don't need to keep the leads in memory
            # Try to avoid to explode memory usage
            self.env.invalidate_all()
            _logger.info(
                'Team %s: Assigned %s leads based on preference, on a potential of %s (limited by quota)',
                team.name, len(assigned_preferred_leads), len(preferred_leads)
            )
        _logger.info(
            'Assigned %s leads to %s salesmen',
            sum(len(r['assigned']) for r in result_data.values()), len(result_data)
        )
        for member, member_info in result_data.items():
            _logger.info(
                '-> member %s of team %s: assigned %d/%d leads (%s)',
                member.id, member.crm_team_id.id, len(member_info["assigned"]), member_info["quota"], member_info["assigned"]
            )
        return result_data