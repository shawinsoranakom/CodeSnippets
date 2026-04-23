def _action_assign_leads_logs(self, teams_data, members_data):
        """ Tool method to prepare notification about assignment process result.

        :param teams_data: see ``CrmTeam._allocate_leads()``;
        :param members_data: see ``CrmTeam._assign_and_convert_leads()``;

        :returns: list of formatted logs, ready to be formatted into a nice
        plaintext or html message at caller's will
        :rtype: list[str]
        """
        # extract some statistics
        assigned = sum(len(teams_data[team]['assigned']) + len(teams_data[team]['merged']) for team in teams_data)
        duplicates = sum(len(teams_data[team]['duplicates']) for team in teams_data)
        members = len(members_data)
        members_assigned = sum(len(member_data['assigned']) for member_data in members_data.values())

        # format user notification
        message_parts = []
        # 1- duplicates removal
        if duplicates:
            message_parts.append(_("%(duplicates)s duplicates leads have been merged.",
                                   duplicates=duplicates))

        # 2- nothing assigned at all
        if not assigned and not members_assigned:
            if len(self) == 1:
                if not self.assignment_max:
                    message_parts.append(
                        _("No allocated leads to %(team_name)s team because it has no capacity. Add capacity to its salespersons.",
                          team_name=self.name))
                else:
                    message_parts.append(
                        _("No allocated leads to %(team_name)s team and its salespersons because no unassigned lead matches its domain.",
                          team_name=self.name))
            else:
                message_parts.append(
                    _("No allocated leads to any team or salesperson. Check your Sales Teams and Salespersons configuration as well as unassigned leads."))

        # 3- team allocation
        if not assigned and members_assigned:
            if len(self) == 1:
                message_parts.append(
                    _("No new lead allocated to %(team_name)s team because no unassigned lead matches its domain.",
                      team_name=self.name))
            else:
                message_parts.append(_("No new lead allocated to the teams because no lead match their domains."))
        elif assigned:
            if len(self) == 1:
                message_parts.append(
                    _("%(assigned)s leads allocated to %(team_name)s team.",
                      assigned=assigned, team_name=self.name))
            else:
                message_parts.append(
                    _("%(assigned)s leads allocated among %(team_count)s teams.",
                      assigned=assigned, team_count=len(self)))

        # 4- salespersons assignment
        if not members_assigned and assigned:
            message_parts.append(
                _("No lead assigned to salespersons because no unassigned lead matches their domains."))
        elif members_assigned:
            message_parts.append(
                _("%(members_assigned)s leads assigned among %(member_count)s salespersons.",
                  members_assigned=members_assigned, member_count=members))

        return message_parts