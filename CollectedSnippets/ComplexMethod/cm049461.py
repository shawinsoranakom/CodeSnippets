def _contact_iap(local_endpoint, params):
            # mock single sms sending
            if local_endpoint == '/iap/message_send':
                self._sms += [{
                    'number': number,
                    'body': params['message'],
                } for number in params['numbers']]
                return True  # send_message v0 API returns always True
            # mock batch sending
            if local_endpoint == '/iap/sms/2/send':
                result = []
                for to_send in params['messages']:
                    res = {'res_id': to_send['res_id'], 'state': 'delivered' if force_delivered else 'success', 'credit': 1}
                    error = sim_error or (nbr_t_error and nbr_t_error.get(to_send['number']))
                    if error and error == 'credit':
                        res.update(credit=0, state='insufficient_credit')
                    elif error and error in {'wrong_number_format', 'unregistered', 'server_error'}:
                        res.update(state=error)
                    elif error and error == 'jsonrpc_exception':
                        raise exceptions.AccessError(
                            'The url that this service requested returned an error. Please contact the author of the app. The url it tried to contact was ' + local_endpoint
                        )
                    result.append(res)
                    if res['state'] == 'success' or res['state'] == 'delivered':
                        self._sms.append({
                            'number': to_send['number'],
                            'body': to_send['content'],
                        })
                return result
            elif local_endpoint == '/api/sms/3/send':
                result = []
                for message in params['messages']:
                    for number in message["numbers"]:
                        error = sim_error or (nbr_t_error and nbr_t_error.get(number['number']))
                        if error == 'jsonrpc_exception':
                            raise exceptions.AccessError(
                                'The url that this service requested returned an error. '
                                'Please contact the author of the app. '
                                'The url it tried to contact was ' + local_endpoint
                            )
                        elif error == 'credit':
                            error = 'insufficient_credit'
                        res = {
                            'uuid': number['uuid'],
                            'state': error or ('delivered' if force_delivered else 'success' if not moderated else 'processing'),
                            'credit': 1,
                        }
                        if error:
                            # credit is only given if the amount is known
                            res.update(credit=0)
                        else:
                            self._sms.append({
                                'number': number['number'],
                                'body': message['content'],
                                'uuid': number['uuid'],
                            })
                        result.append(res)
                return result