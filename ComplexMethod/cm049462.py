def _send_with_api(self, sms_api, unlink_failed=False, unlink_sent=True, raise_exception=False):
        """Send SMS after checking the number (presence and formatting)."""
        messages = [{
            'content': body,
            'numbers': [{'number': sms.number, 'uuid': sms.uuid} for sms in body_sms_records],
        } for body, body_sms_records in self.grouped('body').items()]

        delivery_reports_url = url_join(self[0].get_base_url(), '/sms/status')
        try:
            results = sms_api._send_sms_batch(messages, delivery_reports_url=delivery_reports_url)
        except Exception as e:
            _logger.info('Sent batch %s SMS: %s: failed with exception %s', len(self.ids), self.ids, e)
            if raise_exception:
                raise
            results = [{'uuid': sms.uuid, 'state': 'server_error'} for sms in self]
        else:
            _logger.info('Send batch %s SMS: %s: gave %s', len(self.ids), self.ids, results)

        results_uuids = [result['uuid'] for result in results]
        all_sms_sudo = self.env['sms.sms'].sudo().search([('uuid', 'in', results_uuids)]).with_context(sms_skip_msg_notification=True)

        for (iap_state, failure_reason), results_group in tools.groupby(results, key=lambda result: (result['state'], result.get('failure_reason'))):
            sms_sudo = all_sms_sudo.filtered(lambda s: s.uuid in {result['uuid'] for result in results_group})
            if success_state := self.IAP_TO_SMS_STATE_SUCCESS.get(iap_state):
                sms_sudo.sms_tracker_id._action_update_from_sms_state(success_state)
                to_delete = {'to_delete': True} if unlink_sent else {}
                sms_sudo.write({'state': success_state, 'failure_type': False, **to_delete})
            else:
                failure_type = sms_api.PROVIDER_TO_SMS_FAILURE_TYPE.get(iap_state, 'unknown')
                if failure_type != 'unknown':
                    sms_sudo.sms_tracker_id._action_update_from_sms_state('error', failure_type=failure_type, failure_reason=failure_reason)
                else:
                    sms_sudo.sms_tracker_id.with_context(sms_known_failure_reason=failure_reason)._action_update_from_provider_error(iap_state)
                to_delete = {'to_delete': True} if unlink_failed else {}
                sms_sudo.write({'state': 'error', 'failure_type': failure_type, **to_delete})

        all_sms_sudo._handle_call_result_hook(results)
        all_sms_sudo.mail_message_id._notify_message_notification_update()