def _notify_get_recipients_groups(self, message, model_description, msg_vals=False):
        # Tweak 'view document' button for portal customers, calling directly routes for confirm specific to PO model.
        groups = super()._notify_get_recipients_groups(
            message, model_description, msg_vals=msg_vals
        )
        if not self:
            return groups

        self.ensure_one()
        try:
            customer_portal_group = next(group for group in groups if group[0] == 'portal_customer')
        except StopIteration:
            pass
        else:
            access_opt = customer_portal_group[2].setdefault('button_access', {})
            if self.env.context.get('is_reminder'):
                access_opt['title'] = _('View')
            else:
                access_opt.update(
                    title=_("View Quotation") if self.state in ('draft', 'sent') else _("View Order"),
                    url=self.get_base_url() + self.get_confirm_url(),
                )

        return groups