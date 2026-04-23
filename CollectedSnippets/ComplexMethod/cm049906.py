def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        """ Optional method to override in addons inheriting from mail.thread.
        Return a list tuples containing (
          partner ID,
          subtype IDs (or False if model-based default subtypes),
          QWeb template XML ID for notification (or False is no specific
            notification is required),
          ), aka partners and their subtype and possible notification to send
        using the auto subscription mechanism linked to updated values.

        Default value of this method is to return the new responsible of
        documents. This is done using relational fields linking to res.users
        with tracking set. It is considered as being
        responsible for the document and therefore standard behavior is to
        subscribe the user and send them a notification.

        Override this method to change that behavior and/or to add people to
        notify, using possible custom notification.

        :param updated_values: see ``_message_auto_subscribe``
        :param default_subtype_ids: coming from ``_get_auto_subscription_subtypes``
        """
        fnames = []
        field = self._fields.get('user_id')
        user_id = updated_values.get('user_id')
        if field and user_id and field.comodel_name == 'res.users' and getattr(field, 'tracking', False):
            user = self.env['res.users'].sudo().browse(user_id)
            try: # avoid to make an exists, lets be optimistic and try to read it.
                if user.active:
                    return [(user.partner_id.id, default_subtype_ids, 'mail.message_user_assigned' if user != self.env.user else False)]
            except:
                pass
        return []