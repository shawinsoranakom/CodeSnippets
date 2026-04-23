def _contact_iap(local_endpoint, action, params, timeout):
            sim_result = {
                'website': 'https://www.heinrich.de',
                'city': 'Mönchengladbach',
                'email': False,
                'logo': 'https://logo.clearbit.com/heinrichsroofing.com',
                'name': 'Heinrich',
                'zip': '41179',
                'phone': '+49 0000 112233',
                'street': 'Mennrather Str. 123456',
                'country_code': self.base_de.code,
                'country_name': self.base_de.name,
                'state_id': False,
            }
            if default_data:
                sim_result.update(default_data)
            # mock enrich only currently, to update further
            if action == 'enrich_by_domain':
                if sim_error and sim_error == 'credit':
                    raise iap_tools.InsufficientCreditError('InsufficientCreditError')
                elif sim_error and sim_error == 'jsonrpc_exception':
                    raise exceptions.AccessError(
                        'The url that this service requested returned an error. Please contact the author of the app. The url it tried to contact was ' + local_endpoint
                    )
                elif sim_error and sim_error == 'token':
                    raise ValueError('No account token')
                return {'data': sim_result}