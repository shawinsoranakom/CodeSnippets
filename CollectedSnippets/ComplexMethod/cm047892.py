def _get_rules_payload(self):
        company_country = self.env.company.country_id
        rule_payload = {}
        for rule in self:
            # accumulate all reveal_ids (separated by ',') into one list
            # eg: 3 records with values: "175,176", "177" and "190,191"
            # will become ['175','176','177','190','191']
            reveal_ids = [
                reveal_id.strip()
                for reveal_ids in rule.mapped('industry_tag_ids.reveal_ids')
                for reveal_id in reveal_ids.split(',')
            ]
            data = {
                'rule_id': rule.id,
                'lead_for': rule.lead_for,
                'countries': rule.country_ids.mapped('code'),
                'filter_on_size': rule.filter_on_size,
                'company_size_min': rule.company_size_min,
                'company_size_max': rule.company_size_max,
                'industry_tags': reveal_ids,
                'user_country': company_country and company_country.code or False
            }
            if rule.lead_for == 'people':
                data.update({
                    'contact_filter_type': rule.contact_filter_type,
                    'preferred_role': rule.preferred_role_id.reveal_id or '',
                    'other_roles': rule.other_role_ids.mapped('reveal_id'),
                    'seniority': rule.seniority_id.reveal_id or '',
                    'extra_contacts': rule.extra_contacts - 1
                })
            rule_payload[rule.id] = data
        return rule_payload