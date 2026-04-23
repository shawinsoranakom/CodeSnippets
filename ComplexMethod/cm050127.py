def _manage_mail_values(self, mail_values_all):
        # Filter out canceled messages of mass mailing and create traces for canceled ones.
        results = super()._manage_mail_values(mail_values_all)
        if not self._is_mass_mailing():
            return results
        self.env['mailing.trace'].sudo().create([
            trace_commands[0][2]
            for mail_values in results.values()
            if (mail_values.get('state') == 'cancel' and (trace_commands := mail_values['mailing_trace_ids'])
                # Ensure it is a create command
                and len(trace_commands) == 1 and len(trace_commands[0]) == 3 and trace_commands[0][0] == 0)
        ])
        return {
            res_id: mail_values
            for res_id, mail_values in results.items()
            if mail_values.get('state') != 'cancel'
        }