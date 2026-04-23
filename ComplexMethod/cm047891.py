def _match_url(self, website_id, url, country_code, state_code, rules_excluded):
        """
        Return the matching rule based on the country, the website and URL.
        """
        all_rules = self._get_active_rules()
        rules_id = all_rules['country_rules'].get(country_code, [])

        rules_matched = []
        for rule_index in rules_id:
            rule = all_rules['rules'][rule_index]
            if ((country_code, state_code) in rule['state_codes'] or (country_code, False) in rule['state_codes'])\
                and (not rule['website_id'] or rule['website_id'] == website_id)\
                and str(rule['id']) not in rules_excluded\
                and re.search(rule['regex'], url):
                rules_matched.append(rule)
        return rules_matched