def _constrains_membership(self):
        # In mono membership mode: check crm_team_id / user_id is unique for active
        # memberships. Inactive memberships can create duplicate pairs which is whyy
        # we don't use a SQL constraint. Include "self" in search in case we use create
        # multi with duplicated user / team pairs in it. Use an explicit active leaf
        # in domain as we may have an active_test in context that would break computation
        existing = self.env['crm.team.member'].search([
            ('crm_team_id', 'in', self.crm_team_id.ids),
            ('user_id', 'in', self.user_id.ids),
            ('active', '=', True)
        ])
        duplicates = self.env['crm.team.member']

        active_records = dict(
            (membership.user_id.id, membership.crm_team_id.id)
            for membership in self if membership.active
        )
        for membership in self:
            potential = existing.filtered(lambda m: m.user_id == membership.user_id and \
                m.crm_team_id == membership.crm_team_id and m.id != membership.id
            )
            if not potential or len(potential) > 1:
                duplicates += potential
                continue
            if active_records.get(potential.user_id.id):
                duplicates += potential
            else:
                active_records[potential.user_id.id] = potential.crm_team_id.id

        if duplicates:
            raise exceptions.ValidationError(
                _("You are trying to create duplicate membership(s). We found that %(duplicates)s already exist(s).",
                  duplicates=", ".join("%s (%s)" % (m.user_id.name, m.crm_team_id.name) for m in duplicates)
                 ))