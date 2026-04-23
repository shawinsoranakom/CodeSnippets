def _get_active_rules(self):
        """
        Returns informations about the all rules.
        The return is in the form :
        {
            'country_rules': {
                'BE': [0, 1],
                'US': [0]
            },
            'rules': [
            {
                'id': 0,
                'regex': ***,
                'website_id': 1,
                'country_codes': ['BE', 'US'],
                'state_codes': [('BE', False), ('US', 'NY'), ('US', 'CA')]
            },
            {
                'id': 1,
                'regex': ***,
                'website_id': 1,
                'country_codes': ['BE'],
                'state_codes': [('BE', False)]
            }
            ]
        }
        """
        country_rules = {}
        rules_records = self.search([])
        rules = []
        # Fixes for special cases
        for rule in rules_records:
            regex_url = rule['regex_url']
            if not regex_url:
                regex_url = '.*'    # for all pages if url not given
            elif regex_url == '/':
                regex_url = '.*/$'  # for home
            countries = rule.country_ids.mapped('code')

            # First apply rules for any state in countries
            states = [(country_id.code, False) for country_id in rule.country_ids]
            if rule.state_ids:
                for state_id in rule.state_ids:
                    if (state_id.country_id.code, False) in states:
                        # Remove country because rule doesn't apply to any state
                        states.remove((state_id.country_id.code, False))
                    states += [(state_id.country_id.code, state_id.code)]

            rules.append({
                'id': rule.id,
                'regex': regex_url,
                'website_id': rule.website_id.id if rule.website_id else False,
                'country_codes': countries,
                'state_codes': states
            })
            for country in countries:
                country_rules = self._add_to_country(country_rules, country, len(rules) - 1)
        return {
            'country_rules': country_rules,
            'rules': rules,
        }