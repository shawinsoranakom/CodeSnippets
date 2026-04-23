def _message_route_process(self, message, message_dict, routes):
        self = self.with_context(attachments_mime_plainxml=True) # import XML attachments as text
        # postpone setting message_dict.partner_ids after message_post, to avoid double notifications
        original_partner_ids = message_dict.pop('partner_ids', [])
        thread_id = False
        for model, thread_id, custom_values, user_id, alias in routes or ():
            subtype_id = False
            related_user = self.env['res.users'].browse(user_id)
            Model = self.env[model].with_context(mail_create_nosubscribe=True, mail_create_nolog=True)
            if not (thread_id and hasattr(Model, 'message_update') or hasattr(Model, 'message_new')):
                raise ValueError(
                    "Undeliverable mail with Message-Id %s, model %s does not accept incoming emails" %
                    (message_dict['message_id'], model)
                )

            # disabled subscriptions during message_new/update to avoid having the system user running the
            # email gateway become a follower of all inbound messages
            ModelCtx = Model.with_user(related_user).sudo()
            if thread_id and hasattr(ModelCtx, 'message_update'):
                thread = ModelCtx.browse(thread_id)
                thread.message_update(message_dict)
            else:
                # if a new thread is created, parent is irrelevant
                message_dict.pop('parent_id', None)
                # Report failure/record success of message creation except if alias is not defined (fallback model case)
                try:
                    thread = ModelCtx.message_new(message_dict, custom_values)
                except Exception:
                    if alias:
                        with self.pool.cursor() as new_cr:
                            self.with_env(self.env(cr=new_cr)).env['mail.alias'].browse(alias.id
                            )._alias_bounce_incoming_email(message, message_dict, set_invalid=True)
                    raise
                else:
                    if alias and alias.alias_status != 'valid':
                        alias.alias_status = 'valid'
                thread_id = thread.id
                subtype_id = thread._creation_subtype().id

            # switch to odoobot for all incoming message creation
            # to have a high-privilege archived user so real_author_id is correctly computed
            thread_root = thread.with_user(self.env.ref('base.user_root'))
            # replies to internal message are considered as notes, otherwise they are comments
            parent_message = False
            if message_dict.get('parent_id'):
                parent_message = self.env['mail.message'].sudo().browse(message_dict['parent_id'])
            partner_ids = []
            if not subtype_id:
                if message_dict.get('is_internal'):
                    subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
                else:
                    subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
            # additional recipients
            # - internal: ping parent message author to ensure they are notified of a private answer
            # - from a customer: ping parent message author to be sure he is notified (will be removed
            # if already follower or notified through incoming_email_to/cc)
            if parent_message and parent_message.author_id:
                if message_dict.get('is_internal'):
                    partner_ids = [parent_message.author_id.id]
                elif parent_message.author_id.partner_share:
                    partner_ids = [parent_message.author_id.id]

            post_params = dict(
                incoming_email_cc=message_dict.pop('cc_filtered', False),
                incoming_email_to=message_dict.pop('to_filtered', False),
                subtype_id=subtype_id,
                partner_ids=partner_ids,
                **message_dict,
            )
            # remove computational values not stored on mail.message and avoid warnings when creating it
            for x in ('from', 'recipients',
                      'cc', 'to',  # use cc_filtered, to_filtered
                      'references', 'in_reply_to', 'x_odoo_message_id',
                      'is_bounce', 'bounced_email', 'bounced_message', 'bounced_msg_ids', 'bounced_partner'):
                post_params.pop(x, None)
            new_msg = False
            if thread_root._name == 'mail.thread':  # message with parent_id not linked to record
                new_msg = thread_root.message_notify(**post_params)
            else:
                # if no author, skip any author subscribe check; otherwise message_post
                # checks anyway for real author and filters inactive (like odoobot)
                thread_root = thread_root.with_context(mail_post_autofollow_author_skip=not message_dict.get('author_id'))
                new_msg = thread_root.message_post(**post_params)

            if new_msg and original_partner_ids:
                # postponed after message_post, because this is an external message and we don't want to create
                # duplicate emails due to notifications
                new_msg.write({'partner_ids': original_partner_ids})
        return thread_id