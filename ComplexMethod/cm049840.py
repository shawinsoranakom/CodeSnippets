def _message_fetch(self, domain, *, thread=None, search_term=None, is_notification=None, before=None, after=None, around=None, limit=30):
        res = {}
        domain = Domain(True if domain is None else domain)
        if thread:
            domain &= (
                Domain("res_id", "=", thread.id)
                & Domain("model", "=", thread._name)
                & Domain("message_type", "!=", "user_notification")
            )
        if is_notification is True:
            domain &= Domain("message_type", "=", "notification")
        elif is_notification is False:
            domain &= Domain("message_type", "!=", "notification")
        if search_term:
            # we replace every space by a % to avoid hard spacing matching
            search_term = search_term.replace(" ", "%")
            message_domain = Domain.OR([
                # sudo: access to attachment is allowed if you have access to the parent model
                [("attachment_ids", "in", self.env["ir.attachment"].sudo()._search([("name", "ilike", search_term)]))],
                [("body", "ilike", search_term)],
                [("subject", "ilike", search_term)],
                [("subtype_id.description", "ilike", search_term)],
            ])
            if thread and is_notification is not False:
                tracking_value_domain = (
                    Domain("mail_message_id.res_id", "=", thread.id)
                    & Domain("mail_message_id.model", "=", thread._name)
                    & self._get_tracking_values_domain(search_term)
                )
                # sudo: mail.tracking.value - searching allowed tracking values for acessible records
                tracking_values = self.env["mail.tracking.value"].sudo().search(tracking_value_domain)
                accessible_tracking_value_ids = tracking_values._filter_has_field_access(self.env)
                message_domain |= Domain("id", "in", accessible_tracking_value_ids.mail_message_id.ids)
            domain &= message_domain
            res["count"] = self.search_count(domain)
        if around is not None:
            messages_before = self.search(domain & Domain('id', '<=', around), limit=limit // 2, order="id DESC")
            messages_after = self.search(domain & Domain('id', '>', around), limit=limit // 2, order='id ASC')
            return {**res, "messages": (messages_after + messages_before).sorted('id', reverse=True)}
        if before:
            domain &= Domain('id', '<', before)
        if after:
            domain &= Domain('id', '>', after)
        res["messages"] = self.search(domain, limit=limit, order='id ASC' if after else 'id DESC')
        if after:
            res["messages"] = res["messages"].sorted('id', reverse=True)
        return res