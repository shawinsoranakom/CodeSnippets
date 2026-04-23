def _prepare_iap_payload(self):
        """
        This will prepare the data to send to the server
        """
        self.ensure_one()
        payload = {
            'lead_number': self.lead_number,
            'search_type': self.search_type,
            'countries': [{
                'code': country.code,
                'states': self.state_ids.filtered(lambda state: state in country.state_ids).mapped('code'),
            } for country in self.country_ids],
        }

        if self.filter_on_size:
            payload.update({'company_size_min': self.company_size_min,
                            'company_size_max': self.company_size_max})
        if self.industry_ids:
            # accumulate all reveal_ids (separated by ',') into one list
            # eg: 3 records with values: "175,176", "177" and "190,191"
            # will become ['175','176','177','190','191']
            all_industry_ids = [
                reveal_id.strip()
                for reveal_ids in self.mapped('industry_ids.reveal_ids')
                for reveal_id in reveal_ids.split(',')
            ]
            payload['industry_ids'] = all_industry_ids
        if self.search_type == 'people':
            payload.update({'contact_number': self.contact_number,
                            'contact_filter_type': self.contact_filter_type})
            if self.contact_filter_type == 'role':
                payload.update({'preferred_role': self.preferred_role_id.reveal_id,
                                'other_roles': self.role_ids.mapped('reveal_id')})
            elif self.contact_filter_type == 'seniority':
                payload['seniority'] = self.seniority_id.reveal_id
        return payload