def prepare_pls_tooltip_data(self):
        """
        Compute and return all necessary information to render CrmPlsTooltip, displayed when
        pressing the small AI button, located next to the label of probability when automated,
        in the crm.lead form view. This method first replaces ids with display names of relational
        fields before returning data, then also recomputes probabilities and writes them on self.

        :returns:

            ::
                {
                    low_3_data: list of field-value couples for lowest 3 criterions, lowest first
                    probability: numerical value, used for display on tooltip
                    team_name: string, name of lead team if any
                    top_3_data: list of field-value couples for top 3 criterions, highest first
                }

        :rtype: dict
        """
        self.ensure_one()
        _unused, tooltip_data = self._pls_get_naive_bayes_probabilities(is_tooltip=True)
        sorted_scores_with_name = []

        # We want to display names in the tooltip, not ids.
        # The last element in tuple is only used for tags to ensure same color in tooltip.
        for score, field, value in sorted(tooltip_data['scores']):
            # Skip nonsense results for phone and email states. May happen in a db having a few leads.
            if field in ['phone_state', 'email_state']:
                if value in [False, 'incorrect'] and tools.float_compare(score, 0.50, 2) > 0:
                    continue
                if value == 'correct' and tools.float_compare(score, 0.50, 2) < 0:
                    continue
            if field == 'tag_id':
                tag = self.tag_ids.filtered(lambda tag: tag.id == value)
                sorted_scores_with_name.append((score, field, tag.display_name, tag.color))
            elif isinstance(self[field], models.BaseModel):
                sorted_scores_with_name.append((score, field, self[field].display_name, False))
            else:
                sorted_scores_with_name.append((score, field, str(value), False))

        # Update automated probability, as it may have changed since last computation
        # -> avoids differences in display between tooltip and record. A 0.00 probability implies
        # that the computation was not possible. Sample data will be used instead.
        probability_values = {'automated_probability': tooltip_data['probability']}
        if self.is_automated_probability:
            probability_values['probability'] = tooltip_data['probability']
        self.write(probability_values)

        # Sample values if probability could not be computed. If it was, but if all scores
        # were excluded above, a placeholder will be used instead in the tooltip.
        if tools.float_is_zero(tooltip_data['probability'], 2):
            sorted_scores_with_name = [
                (.1, 'email_state', False, False),
                (.2, 'tag_id', _('Exploration'), 4),
                (.3, 'stage_id', _('New'), False),
                (.7, 'phone_state', 'correct', False),
                (.8, 'country_id', _('Belgium'), False),
                (.9, 'tag_id', _('Consulting'), 3),
            ]

        return {
            'low_3_data': [
                {
                    'field': element[1],
                    'value': element[2],
                    'color': element[3]
                } for element in sorted_scores_with_name[:3] if tools.float_compare(element[0], 0.50, 2) < 0
            ],
            'probability': tooltip_data['probability'],
            'team_name': self.team_id.display_name,
            'top_3_data': [
                {
                    'field': element[1],
                    'value': element[2],
                    'color': element[3]
                } for element in sorted_scores_with_name[::-1][:3] if tools.float_compare(element[0], 0.50, 2) > 0
            ],
        }