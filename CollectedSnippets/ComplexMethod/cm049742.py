def _action_send_mail_comment(self, res_ids):
        """ Send in comment mode. It calls message_post on model, or the generic
        implementation of it if not available (as message_notify). """
        self.ensure_one()
        post_values_all = self._manage_mail_values(self._prepare_mail_values(res_ids))
        ActiveModel = self.env[self.model] if self.model and hasattr(self.env[self.model], 'message_post') else self.env['mail.thread']
        if self.composition_batch:
            # add context key to avoid subscribing the author
            ActiveModel = ActiveModel.with_context(
                mail_post_autofollow_author_skip=True,
            )
        messages = self.env['mail.message']
        for res_id, post_values in post_values_all.items():
            if ActiveModel._name == 'mail.thread':
                post_values.pop('message_type')  # forced to user_notification
                post_values.pop('parent_id', False)  # not supported in notify
                if self.model:
                    post_values['model'] = self.model
                    post_values['res_id'] = res_id
                message = ActiveModel.message_notify(**post_values)
                if not message:
                    # if message_notify returns an empty record set, no recipients where found.
                    raise UserError(_("No recipient found."))
                messages += message
            else:
                messages += ActiveModel.browse(res_id).message_post(**post_values)
        return messages