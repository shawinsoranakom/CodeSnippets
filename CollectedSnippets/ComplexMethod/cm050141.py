def _action_view_documents_filtered(self, view_filter):
        def _fetch_trace_res_ids(trace_domain):
            trace_domain &= Domain('mass_mailing_id', '=', self.id)
            return self.env['mailing.trace'].search_fetch(domain=trace_domain, field_names=['res_id']).mapped('res_id')

        model_name = self.env['ir.model']._get(self.mailing_model_real).display_name
        helper_header = None
        helper_message = None
        if view_filter == 'reply':
            res_ids = _fetch_trace_res_ids(Domain('trace_status', '=', 'reply'))
            helper_header = _("No %s replied to your mailing yet!", model_name)
            helper_message = _("To track how many replies this mailing gets, make sure "
                               "its reply-to address belongs to this database.")
        elif view_filter == 'bounce':
            res_ids = _fetch_trace_res_ids(Domain('trace_status', '=', 'bounce'))
            helper_header = _("No %s address bounced yet!", model_name)
            helper_message = _("Bounce happens when a mailing cannot be delivered (fake address, "
                               "server issues, ...). Check each record to see what went wrong.")
        elif view_filter == 'clicked':
            res_ids = _fetch_trace_res_ids(Domain('links_click_ids', '!=', False))
            helper_header = _("No %s clicked your mailing yet!", model_name)
            helper_message = _(
                "Come back once your mailing has been sent to track who clicked on the embedded links.")
        elif view_filter == 'open':
            res_ids = _fetch_trace_res_ids(Domain('trace_status', 'in', ('open', 'reply')))
            helper_header = _("No %s opened your mailing yet!", model_name)
            helper_message = _("Come back once your mailing has been sent to track who opened your mailing.")
        elif view_filter == 'delivered':
            res_ids = _fetch_trace_res_ids(Domain('trace_status', 'in', ('sent', 'open', 'reply')))
            helper_header = _("No %s received your mailing yet!", model_name)
            helper_message = _("Wait until your mailing has been sent to check how many recipients you managed to reach.")
        elif view_filter == 'sent':
            res_ids = _fetch_trace_res_ids(Domain('sent_datetime', '!=', False))
        else:
            res_ids = []

        action = {
            'name': model_name,
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': self.mailing_model_real,
            'domain': [('id', 'in', res_ids)],
            'context': dict(self.env.context, create=False),
        }
        if helper_header and helper_message:
            action['help'] = Markup('<p class="o_view_nocontent_smiling_face">%s</p><p>%s</p>') % (
                helper_header, helper_message,
            ),
        return action