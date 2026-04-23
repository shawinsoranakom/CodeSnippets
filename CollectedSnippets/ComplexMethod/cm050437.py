def _pls_update_frequency_table(self, new_frequencies_by_team, step, existing_frequencies_by_team=None):
        """ Create / update the frequency table in a cross company way, per team_id"""
        values_to_update = {}
        values_to_create = []
        if not existing_frequencies_by_team:
            existing_frequencies_by_team = {}
        # build the create multi + frequencies to update
        for team_id, new_frequencies in new_frequencies_by_team.items():
            for field, value in new_frequencies.items():
                # frequency already present ?
                current_frequencies = existing_frequencies_by_team.get(team_id, {})
                for param, result in value.items():
                    current_frequency_for_couple = current_frequencies.get(field, {}).get(param, {})
                    # If frequency already present : UPDATE IT
                    if current_frequency_for_couple:
                        new_won = current_frequency_for_couple['won'] + (result['won'] * step)
                        new_lost = current_frequency_for_couple['lost'] + (result['lost'] * step)
                        # ensure to have always positive frequencies
                        values_to_update[current_frequency_for_couple['frequency_id']] = {
                            'won_count': new_won if new_won > 0 else 0.1,
                            'lost_count': new_lost if new_lost > 0 else 0.1
                        }
                        continue

                    # Else, CREATE a new frequency record.
                    # We add + 0.1 in won and lost counts to avoid zero frequency issues
                    # should be +1 but it weights too much on small recordset.
                    values_to_create.append({
                        'variable': field,
                        'value': param,
                        'won_count': result['won'] + 0.1,
                        'lost_count': result['lost'] + 0.1,
                        'team_id': team_id if team_id else None  # team_id = 0 means no team_id
                    })

        LeadScoringFrequency = self.env['crm.lead.scoring.frequency'].sudo()
        for frequency_id, values in values_to_update.items():
            LeadScoringFrequency.browse(frequency_id).write(values)

        if values_to_create:
            LeadScoringFrequency.create(values_to_create)