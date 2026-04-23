def _filter_out_and_handle_revoked_sms_values(self, sms_values_all):
        # Filter out canceled sms of mass mailing and create traces for canceled ones.
        results = super()._filter_out_and_handle_revoked_sms_values(sms_values_all)
        if not self._is_mass_sms():
            return results
        self.env['mailing.trace'].sudo().create([
            trace_commands[0][2]
            for mail_values in results.values()
            if mail_values.get('state') == 'canceled' and mail_values['mailing_trace_ids']
            for trace_commands in (mail_values['mailing_trace_ids'],)
            # Ensure it is a create command
            if len(trace_commands) == 1 and len(trace_commands[0]) == 3 and trace_commands[0][0] == 0
        ])
        return {
            res_id: sms_values
            for res_id, sms_values in results.items()
            if sms_values.get('state') != 'canceled'
        }