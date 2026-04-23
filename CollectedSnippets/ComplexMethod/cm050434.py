def _pls_get_naive_bayes_probabilities(self, batch_mode=False, is_tooltip=False):
        """
        In machine learning, naive Bayes classifiers (NBC) are a family of simple "probabilistic classifiers" based on
        applying Bayes theorem with strong (naive) independence assumptions between the variables taken into account.
        E.g: will TDE eat m&m's depending on his sleep status, the amount of work he has and the fullness of his stomach?
        As we use experience to compute the statistics, every day, we will register the variables state + the result.
        As the days pass, we will be able to determine, with more and more precision, if TDE will eat m&m's
        for a specific combination :
            - did sleep very well, a lot of work and stomach full > Will never happen !
            - didn't sleep at all, no work at all and empty stomach > for sure !
        Following Bayes' Theorem: the probability that an event occurs (to win) under certain conditions is proportional
        to the probability to win under each condition separately and the probability to win. We compute a 'Win score'
        -> P(Won | A∩B) ∝ P(A∩B | Won)*P(Won) OR S(Won | A∩B) = P(A∩B | Won)*P(Won)
        To compute a percentage of probability to win, we also compute the 'Lost score' that is proportional to the
        probability to lose under each condition separately and the probability to lose.
        -> Probability =  S(Won | A∩B) / ( S(Won | A∩B) + S(Lost | A∩B) )
        See https://www.youtube.com/watch?v=CPqOCI0ahss can help to get a quick and simple example.
        One issue about NBC is when a event occurence is never observed.
        E.g: if when TDE has an empty stomach, he always eat m&m's, than the "not eating m&m's when empty stomach' event
        will never be observed.
        This is called 'zero frequency' and that leads to division (or at least multiplication) by zero.
        To avoid this, we add 0.1 in each frequency. With few data, the computation is than not really realistic.
        The more we have records to analyse, the more the estimation will be precise.

        :param bool is_tooltip: If true, method recomputes the probability of self, that should be a singleton, and
            also returns a dict containing probability, and a list of all (score, field, value) triplets for all value of
            PLS fields that impact the computation of the probability. Score is a simple value that indicates whether the
            impact is positive (>.5) or negative (<.5). See method prepare_pls_tooltip_data, or test_pls_tooltip_data for
            more details

        :return: probability in percent (and rounded at 2 decimals) that the lead will be won at the current stage.
        """
        lead_probabilities = {}
        if not self:
            return lead_probabilities

        # Initialize tooltip data. A returned 0.00 probability means computation was not possible.
        tooltip_data = {}
        if is_tooltip:
            self.ensure_one()
            tooltip_data = {
                'probability': 0.0,
                'scores': [],
            }

        # Get all leads values, no matter the team_id
        domain = []
        if batch_mode:
            domain = [
                ('active', '=', True),
                ('id', 'in', self.ids),
                ('won_status', '=', 'pending'),
            ]
        leads_values_dict = self._pls_get_lead_pls_values(domain=domain)

        if not leads_values_dict:
            return lead_probabilities

        # Get unique couples to search in frequency table and won leads.
        leads_fields = set()  # keep unique fields, as a lead can have multiple tag_ids
        won_leads = set()
        won_stage_ids = self.env['crm.stage'].search([('is_won', '=', True)]).ids
        for lead_id, values in leads_values_dict.items():
            for field, value in values['values']:
                if field == 'stage_id' and value in won_stage_ids:
                    won_leads.add(lead_id)
                leads_fields.add(field)
        leads_fields = sorted(leads_fields)
        # get all variable related records from frequency table, no matter the team_id
        frequencies = self.env['crm.lead.scoring.frequency'].search([('variable', 'in', list(leads_fields))], order="team_id asc, id")

        # get all team_ids from frequencies
        frequency_teams = frequencies.mapped('team_id')
        frequency_team_ids = [team.id for team in frequency_teams]

        # restrict to frequencies of lead team if any exist.
        if is_tooltip and self.team_id & frequency_teams:
            frequency_team_ids = [self.team_id.id]
            frequencies = frequencies.filtered(
                lambda frequency: frequency.team_id & self.team_id
            )

        # 1. Compute each variable value count individually
        # regroup each variable to be able to compute their own probabilities
        # As all the variable does not enter into account (as we reject unset values in the process)
        # each value probability must be computed only with their own variable related total count
        # special case: for lead for which team_id is not in frequency table or lead with no team_id,
        # we consider all the records, independently from team_id (this is why we add a result[-1])
        result = dict((team_id, dict((field, dict(won_total=0, lost_total=0)) for field in leads_fields)) for team_id in frequency_team_ids)
        result[-1] = dict((field, dict(won_total=0, lost_total=0)) for field in leads_fields)
        for frequency in frequencies:
            field = frequency['variable']
            value = frequency['value']  # This is always a string

            # To avoid that a tag take too much importance if its subset is too small,
            # we ignore the tag frequencies if we have less than 50 won or lost for this tag.
            if field == 'tag_id' and (frequency['won_count'] + frequency['lost_count']) < 50:
                continue

            if frequency.team_id:
                team_result = result[frequency.team_id.id]
                team_result[field][value] = {'won': frequency['won_count'], 'lost': frequency['lost_count']}
                team_result[field]['won_total'] += frequency['won_count']
                team_result[field]['lost_total'] += frequency['lost_count']

            if value not in result[-1][field]:
                result[-1][field][value] = {'won': 0, 'lost': 0}
            result[-1][field][value]['won'] += frequency['won_count']
            result[-1][field][value]['lost'] += frequency['lost_count']
            result[-1][field]['won_total'] += frequency['won_count']
            result[-1][field]['lost_total'] += frequency['lost_count']

        # Get all won, lost and total count for all records in frequencies per team_id
        for team_id in result:
            result[team_id]['team_won'], \
            result[team_id]['team_lost'], \
            result[team_id]['team_total'] = self._pls_get_won_lost_total_count(result[team_id])

        save_team_id = None
        p_won, p_lost = 1, 1
        for lead_id, lead_values in leads_values_dict.items():
            # if stage_id is null, return 0 and bypass computation
            lead_fields = [value[0] for value in lead_values.get('values', [])]
            if not 'stage_id' in lead_fields:
                lead_probabilities[lead_id] = 0
                continue
            # if lead stage is won, return 100
            elif lead_id in won_leads:
                lead_probabilities[lead_id] = 100
                continue

            # team_id not in frequency Table -> convert to -1
            lead_team_id = lead_values['team_id'] if lead_values['team_id'] in result else -1
            if lead_team_id != save_team_id:
                save_team_id = lead_team_id
                team_won = result[save_team_id]['team_won']
                team_lost = result[save_team_id]['team_lost']
                team_total = result[save_team_id]['team_total']
                # if one count = 0, we cannot compute lead probability
                if not team_won or not team_lost:
                    continue
                p_won = team_won / team_total
                p_lost = team_lost / team_total

            # 2. Compute won and lost score using each variable's individual probability
            s_lead_won, s_lead_lost = p_won, p_lost
            for field, value in lead_values['values']:
                field_result = result.get(save_team_id, {}).get(field)
                value = value.origin if hasattr(value, 'origin') else value
                value_result = field_result.get(str(value)) if field_result else False
                if value_result:
                    total_won = team_won if field == 'stage_id' else field_result['won_total']
                    total_lost = team_lost if field == 'stage_id' else field_result['lost_total']
                    # if one count = 0, we cannot compute lead probability
                    if not total_won or not total_lost:
                        continue
                    p_field_value_won = value_result['won'] / total_won
                    p_field_value_lost = value_result['lost'] / total_lost
                    s_lead_won *= p_field_value_won
                    s_lead_lost *= p_field_value_lost

                    if is_tooltip:
                        score = (
                            1 - p_field_value_lost if field == 'stage_id'
                            else p_field_value_won / (p_field_value_won + p_field_value_lost)
                        )
                        tooltip_data['scores'].append((score, field, value))
            # 3. Compute Probability to win
            probability = s_lead_won / (s_lead_won + s_lead_lost)
            lead_probabilities[lead_id] = min(max(round(100 * probability, 2), 0.01), 99.99)

        if tooltip_data and self.id in lead_probabilities:
            tooltip_data['probability'] = lead_probabilities[self.id]

        return lead_probabilities, tooltip_data