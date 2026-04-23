def _pls_get_lead_pls_values(self, domain=None):
        """
        This methods builds a dict where, for each lead in self or matching the given domain,
        we will get a list of field/value couple.
        Due to onchange and create, we don't always have the id of the lead to recompute.
        When we update few records (one, typically) with onchanges, we build the lead_values (= couple field/value)
        using the ORM.
        To speed up the computation and avoid making too much DB read inside loops,
        we can give a domain to make sql queries to bypass the ORM.
        This domain will be used in sql queries to get the values for every lead matching the domain.
        :param domain: If set, we get all the leads values via unique sql queries (one for tags, one for other fields),
                            using the given domain on leads.
                       If not set, get lead values lead by lead using the ORM.
        :return: {lead_id: [(field1: value1), (field2: value2), ...], ...}
        """
        leads_values_dict = OrderedDict()
        pls_fields = ["stage_id", "team_id"] + self._pls_get_safe_fields()

        # Check if tag_ids is in the pls_fields and removed it from the list. The tags will be managed separately.
        use_tags = 'tag_ids' in pls_fields
        if use_tags:
            pls_fields.remove('tag_ids')

        if domain:
            # Get leads values
            self.flush_model()
            # active_test = False as domain should take active into 'active' field it self
            query = self.env['crm.lead'].with_context(active_test=False)._search(domain, bypass_access=True)
            table = query.table
            query.order = SQL("%(table)s.team_id asc, %(table)s.id desc", table=SQL.identifier(table))
            sql_fields = [SQL.identifier(field) for field in pls_fields]
            self.env.cr.execute(query.select(
                SQL("id"),
                SQL("probability"),
                *sql_fields,
            ))
            lead_results = self.env.cr.dictfetchall()

            if use_tags:
                # Get tags values
                tag_rel_alias = query.left_join(table, 'id', 'crm_tag_rel', 'lead_id', 'crm_tag_rel')
                tag_alias = query.left_join(tag_rel_alias, 'tag_id', 'crm_tag', 'id', 'crm_tag')
                self.env.cr.execute(query.select(
                    SQL("%s AS lead_id", SQL.identifier(table, "id")),
                    SQL("%s AS tag_id", SQL.identifier(tag_alias, "id")),
                ))
                tag_results = self.env.cr.dictfetchall()
            else:
                tag_results = []

            # get all (variable, value) couple for all in self
            for lead in lead_results:
                lead_values = []
                for field in pls_fields + ['probability']:  # add probability as used in _pls_prepare_frequencies (needed in rebuild mode)
                    value = lead[field]
                    if field == 'team_id':  # ignore team_id as stored separately in leads_values_dict[lead_id][team_id]
                        continue
                    if value or field == 'probability':  # 0 is a correct value for probability
                        lead_values.append((field, value))
                    elif field in ('email_state', 'phone_state'):  # As ORM reads 'None' as 'False', do the same here
                        lead_values.append((field, False))
                    leads_values_dict[lead['id']] = {'values': lead_values, 'team_id': lead['team_id'] or 0}

            for tag in tag_results:
                if tag['tag_id']:
                    leads_values_dict[tag['lead_id']]['values'].append(('tag_id', tag['tag_id']))
            return leads_values_dict
        else:
            for lead in self:
                lead_values = []
                for field in pls_fields:
                    if field == 'team_id':  # ignore team_id as stored separately in leads_values_dict[lead_id][team_id]
                        continue
                    value = lead[field].id if isinstance(lead[field], models.BaseModel) else lead[field]
                    if value or field in ('email_state', 'phone_state'):
                        lead_values.append((field, value))
                if use_tags:
                    for tag in lead.tag_ids:
                        lead_values.append(('tag_id', tag.id))
                leads_values_dict[lead.id] = {'values': lead_values, 'team_id': lead['team_id'].id}
            return leads_values_dict