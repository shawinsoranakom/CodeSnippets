def activity_search(self, act_type_xmlids='', user_id=None, additional_domain=None, only_automated=True):
        """ Search automated activities on current record set, given a list of activity
        types xml IDs. It is useful when dealing with specific types involved in automatic
        activities management.

        :param act_type_xmlids: list of activity types xml IDs
        :param user_id: if set, restrict to activities of that user_id;
        :param additional_domain: if set, filter on that domain;
        :param only_automated: if unset, search for all activities, not only automated ones;
        """
        if self.env.context.get('mail_activity_automation_skip'):
            return self.env['mail.activity']

        Data = self.env['ir.model.data'].sudo()
        activity_types_ids = [type_id for type_id in (Data._xmlid_to_res_id(xmlid, raise_if_not_found=False) for xmlid in act_type_xmlids) if type_id]
        if not any(activity_types_ids):
            return self.env['mail.activity']

        domain = Domain([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('activity_type_id', 'in', activity_types_ids)
        ])

        if only_automated:
            domain &= Domain('automated', '=', True)
        if user_id:
            domain &= Domain('user_id', '=', user_id)
        if additional_domain:
            domain &= Domain(additional_domain)

        return self.env['mail.activity'].search(domain)