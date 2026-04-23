def create(self, vals_list):
        """ Synchronize default_list_ids (currently used notably for computed
        fields) default key with subscription_ids given by user when creating
        contacts.

        Those two values have the same purpose, adding a list to to the contact
        either through a direct write on m2m, either through a write on middle
        model subscription.

        This is a bit hackish but is due to default_list_ids key being
        used to compute oupt_out field. This should be cleaned in master but here
        we simply try to limit issues while keeping current behavior. """
        default_list_ids = self.env.context.get('default_list_ids')
        default_list_ids = default_list_ids if isinstance(default_list_ids, (list, tuple)) else []

        for vals in vals_list:
            if vals.get('list_ids') and vals.get('subscription_ids'):
                raise UserError(_('You should give either list_ids, either subscription_ids to create new contacts.'))

        if default_list_ids:
            for vals in vals_list:
                if vals.get('list_ids'):
                    continue
                current_list_ids = []
                subscription_ids = vals.get('subscription_ids') or []
                for subscription in subscription_ids:
                    if len(subscription) == 3:
                        current_list_ids.append(subscription[2]['list_id'])
                for list_id in set(default_list_ids) - set(current_list_ids):
                    subscription_ids.append((0, 0, {'list_id': list_id}))
                vals['subscription_ids'] = subscription_ids

        records = super(MailingContact, self.with_context(default_list_ids=False)).create(vals_list)

        # We need to invalidate list_ids or subscription_ids because list_ids is a many2many
        # using a real model as table ('mailing.subscription') and the ORM doesn't automatically
        # update/invalidate the `list_ids`/`subscription_ids` cache correctly.
        for record in records:
            if record.list_ids:
                record.invalidate_recordset(['subscription_ids'])
            elif record.subscription_ids:
                record.invalidate_recordset(['list_ids'])
        return records