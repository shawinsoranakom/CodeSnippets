def _allocate_leads_deduplicate(self, leads, duplicates_cache=None):
        """ Assign leads to sales team given by self by calling lead tool
        method _handle_salesmen_assignment. In this method we deduplicate leads
        allowing to reduce number of resulting leads before assigning them
        to salesmen.

        :param leads: recordset of leads to assign to current team;
        :param duplicates_cache: if given, avoid to perform a duplicate search
          and fetch information in it instead;
        """
        self.ensure_one()
        duplicates_cache = duplicates_cache if duplicates_cache is not None else dict()

        # classify leads
        leads_assigned = self.env['crm.lead']  # direct team assign
        leads_done_ids, leads_merged_ids, leads_dup_ids = set(), set(), set()  # classification
        leads_dups_dict = dict()  # lead -> its duplicate
        for lead in leads:
            if lead.id not in leads_done_ids:

                # fill cache if not already done
                if lead not in duplicates_cache:
                    duplicates_cache[lead] = lead._get_lead_duplicates(email=lead.email_from)
                lead_duplicates = duplicates_cache[lead].exists()

                if len(lead_duplicates) > 1:
                    leads_dups_dict[lead] = lead_duplicates
                    leads_done_ids.update((lead + lead_duplicates).ids)
                else:
                    leads_assigned += lead
                    leads_done_ids.add(lead.id)

        # assign team to direct assign (leads_assigned) + dups keys (to ensure their team
        # if they are elected master of merge process)
        dups_to_assign = [lead for lead in leads_dups_dict]
        leads_assigned.union(*dups_to_assign)._handle_salesmen_assignment(user_ids=None, team_id=self.id)

        for lead in leads.filtered(lambda lead: lead in leads_dups_dict):
            lead_duplicates = leads_dups_dict[lead]
            merged = lead_duplicates._merge_opportunity(user_id=False, team_id=False, auto_unlink=False, max_length=0)
            leads_dup_ids.update((lead_duplicates - merged).ids)
            leads_merged_ids.add(merged.id)

        return {
            'assigned': set(leads_assigned.ids),
            'merged': leads_merged_ids,
            'duplicates': leads_dup_ids,
        }