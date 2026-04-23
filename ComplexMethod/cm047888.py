def _iap_contact_reveal(params, timeout):
            if sim_error and sim_error == 'credit':
                return {'credit_error': True, 'reveal_data': []}
            if sim_error and sim_error == 'jsonrpc_exception':
                raise exceptions.AccessError(
                    'The url that this service requested returned an error. Please contact the author of the app. The url it tried to contact was [STRIPPED]'
                )
            if sim_error and sim_error == 'no_result':
                return {'credit_error': False, 'reveal_data': []}

            response = []
            for counter, ip_values in enumerate(ip_to_rules):
                ip, rule = ip_values['ip'], ip_values['rules']
                if name_list:
                    base_name = name_list[counter % len(name_list)]
                else:
                    base_name = 'heinrich_%d' % counter

                iap_payload = {
                    'ip': ip,
                    'ip_time_zone': 'Europe/Berlin',
                    'not_found': False,
                    'rule_id': rule.id,
                }
                company_data = self._get_iap_company_data(base_name, service='reveal', add_values={'ip': ip, 'rule': rule})
                if default_data:
                    company_data.update(default_data)
                iap_payload['clearbit_id'] = company_data['clearbit_id']
                iap_payload['reveal_data'] = company_data

                if rule.lead_for == 'people':
                    people_data = self._get_iap_contact_data(base_name, service='reveal')
                    iap_payload['people_data'] = people_data

                iap_payload['credit'] = 1 + (len(people_data) if rule.lead_for == 'people' else 0)

                response.append(iap_payload)

            return {
                'reveal_data': response,
                'credit_error': False
            }