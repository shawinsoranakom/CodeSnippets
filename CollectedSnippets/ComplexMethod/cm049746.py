def _prepare_mail_values_static(self):
        """Prepare values always valid, not rendered or dynamic whatever the
        composition mode and related records.

        :returns: a dict of (field name, value) to be used to populate
          values for each res_id in '_prepare_mail_values';
        :rtype: dict
        """
        self.ensure_one()
        email_mode = self.composition_mode == 'mass_mail'

        if email_mode:
            subtype_id = False
        elif self.subtype_id:
            subtype_id = self.subtype_id.id
        else:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')

        values = {
            'author_id': self.author_id.id,
            'mail_activity_type_id': self.mail_activity_type_id.id,
            'mail_server_id': self.mail_server_id.id,
            'message_type': 'email_outgoing' if email_mode else self.message_type,
            'parent_id': self.parent_id.id,
            'reply_to_force_new': self.reply_to_force_new and bool(self.reply_to),  # if manually voided, fallback on thread-based reply-to computation
            'subtype_id': subtype_id,
        }
        # specific to mass mailing mode
        if email_mode:
            values.update(
                auto_delete=self.auto_delete,
                is_notification=not self.auto_delete or self.auto_delete_keep_log,
                model=self.model,
            )
        # specific to post mode
        else:
            # Several custom layouts make use of the model description at rendering, e.g. in the
            # 'View <document>' button. Some models are used for different business concepts, such as
            # 'purchase.order' which is used for a RFQ and and PO. To avoid confusion, we must use a
            # different wording depending on the state of the object.
            # Therefore, we can set the description in the context from the beginning to avoid falling
            # back on the regular display_name retrieved in ``_notify_by_email_prepare_rendering_context()``.
            model_description = self.env.context.get('model_description')
            values.update(
                email_add_signature=self.email_add_signature,
                email_layout_xmlid=self.email_layout_xmlid,
                force_send=self.force_send,
                mail_auto_delete=self.auto_delete,
                model_description=model_description,
                record_alias_domain_id=self.record_alias_domain_id.id,
                record_company_id=self.record_company_id.id,
            )
            if self.notify_author:  # force only Truthy values, keeping context fallback
                values['notify_author'] = self.notify_author
            if self.notify_author_mention:  # force only Truthy values, keeping context fallback
                values['notify_author_mention'] = self.notify_author_mention
            if self.notify_skip_followers:  # force only Truthy values, no need to bloat with default Falsy
                values['notify_skip_followers'] = self.notify_skip_followers
        return values