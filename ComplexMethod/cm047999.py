def _iap_contact_mining(params, timeout):
            self.assertMineCallParams(params)

            if sim_error and sim_error == 'jsonrpc_exception':
                raise exceptions.AccessError(
                    'The url that this service requested returned an error. Please contact the author of the app. The url it tried to contact was [STRIPPED]'
                )
            if sim_error and sim_error == 'no_result':
                return {'credit_error': False, 'data': []}

            response = []
            for counter in range(0, mine.lead_number):
                if name_list:
                    base_name = name_list[counter % len(name_list)]
                else:
                    base_name = 'heinrich_%d' % counter

                iap_payload = {}
                company_data = self._get_iap_company_data(base_name, service='mine')
                if default_data:
                    company_data.update(default_data)
                response.append(company_data)

            return {
                'data': response,
                'credit_error': sim_error == 'credit',
            }