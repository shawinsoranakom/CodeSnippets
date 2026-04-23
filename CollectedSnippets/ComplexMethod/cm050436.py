def _pls_prepare_update_frequency_table(self, rebuild=False, target_state=False):
        """
        This method is common to Live Increment or Full Rebuild mode, as it shares the main steps.
        This method will prepare the frequency dict needed to update the frequency table:
            - New frequencies: frequencies that we need to add in the frequency table.
            - Existing frequencies: frequencies that are already in the frequency table.
        In rebuild mode, only the new frequencies are needed as existing frequencies are truncated.
        For each team, each dict contains the frequency in won and lost for each field/value couple
        of the target leads.
        Target leads are :
            - in Live increment mode : given ongoing leads (self)
            - in Full rebuild mode : all the closed (won and lost) leads in the DB.
        During the frequencies update, with both new and existing frequencies, we can split frequencies to update
        and frequencies to add. If a field/value couple already exists in the frequency table, we just update it.
        Otherwise, we need to insert a new one.
        """
        # Keep eligible leads
        pls_start_date = self._pls_get_safe_start_date()
        if not pls_start_date:
            return {}, {}

        if rebuild:  # rebuild will treat every closed lead in DB, increment will treat current ongoing leads
            pls_leads = self
        else:
            # Only treat leads created after the PLS start Date
            pls_leads = self.filtered(
                lambda lead: fields.Date.to_date(pls_start_date) <= fields.Date.to_date(lead.create_date))
            if not pls_leads:
                return {}, {}

        # Extract target leads values
        if rebuild:  # rebuild is ok
            domain = [
                ('create_date', '>=', pls_start_date),
                ('won_status', 'in', ['lost', 'won']),
              ]
            team_ids = self.env['crm.team'].with_context(active_test=False).search([]).ids + [0]  # If team_id is unset, consider it as team 0
        else:  # increment
            domain = [('id', 'in', pls_leads.ids)]
            team_ids = pls_leads.mapped('team_id').ids + [0]

        leads_values_dict = pls_leads._pls_get_lead_pls_values(domain=domain)

        # split leads values by team_id
        # get current frequencies related to the target leads
        leads_frequency_values_by_team = dict((team_id, []) for team_id in team_ids)
        leads_pls_fields = set()  # ensure to keep each field unique (can have multiple tag_id leads_values_dict)
        for values in leads_values_dict.values():
            team_id = values.get('team_id', 0)  # If team_id is unset, consider it as team 0
            lead_frequency_values = {'count': 1}
            for field, value in values['values']:
                if field != "probability":  # was added to lead values in batch mode to know won/lost state, but is not a pls fields.
                    leads_pls_fields.add(field)
                else:  # extract lead probability - needed to increment tag_id frequency. (proba always before tag_id)
                    lead_probability = value
                if field == 'tag_id':  # handle tag_id separatelly (as in One Shot rebuild mode)
                    leads_frequency_values_by_team[team_id].append({field: value, 'count': 1, 'probability': lead_probability})
                else:
                    lead_frequency_values[field] = value
            leads_frequency_values_by_team[team_id].append(lead_frequency_values)
        leads_pls_fields = sorted(leads_pls_fields)

        # get new frequencies
        new_frequencies_by_team = {}
        for team_id in team_ids:
            # prepare fields and tag values for leads by team
            new_frequencies_by_team[team_id] = self._pls_prepare_frequencies(
                leads_frequency_values_by_team[team_id], leads_pls_fields, target_state=target_state)

        # get existing frequencies
        existing_frequencies_by_team = {}
        if not rebuild:  # there is no existing frequency in rebuild mode as they were all deleted.
            # read all fields to get everything in memory in one query (instead of having query + prefetch)
            existing_frequencies = self.env['crm.lead.scoring.frequency'].search_read(
                ['&', ('variable', 'in', leads_pls_fields),
                      '|', ('team_id', 'in', pls_leads.mapped('team_id').ids), ('team_id', '=', False)])
            for frequency in existing_frequencies:
                team_id = frequency['team_id'][0] if frequency.get('team_id') else 0
                if team_id not in existing_frequencies_by_team:
                    existing_frequencies_by_team[team_id] = dict((field, {}) for field in leads_pls_fields)

                existing_frequencies_by_team[team_id][frequency['variable']][frequency['value']] = {
                    'frequency_id': frequency['id'],
                    'won': frequency['won_count'],
                    'lost': frequency['lost_count']
                }

        return new_frequencies_by_team, existing_frequencies_by_team