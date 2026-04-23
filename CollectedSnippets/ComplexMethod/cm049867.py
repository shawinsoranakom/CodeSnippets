def create(self, vals_list):
        """ Chatter override :
            - subscribe uid
            - subscribe followers of parent
            - log a creation message
        """
        # when being in 'nosubscribe' mode, also propagate to any message posted
        # during the process, unless specifically asked
        if self.env.context.get('mail_create_nosubscribe') and 'mail_post_autofollow_author_skip' not in self.env.context:
            self = self.with_context(mail_post_autofollow_author_skip=True)

        if self.env.context.get('tracking_disable'):
            threads = super(MailThread, self).create(vals_list)
            threads._track_discard()
            return threads

        threads = super(MailThread, self).create(vals_list)
        # subscribe uid unless asked not to
        if not self.env.context.get('mail_create_nosubscribe') and threads and self.env.user.active and not self.env.user.share:
            self.env['mail.followers']._insert_followers(
                threads._name, threads.ids,
                self.env.user.partner_id.ids, subtypes=None,
                customer_ids=[],
                check_existing=False
            )

        # auto_subscribe: take values and defaults into account
        create_values_list = {}
        for thread, values in zip(threads, vals_list):
            create_values = dict(values)
            for key, val in self.env.context.items():
                if key.startswith('default_') and key[8:] not in create_values:
                    create_values[key[8:]] = val
            thread._message_auto_subscribe(create_values, followers_existing_policy='update')
            create_values_list[thread.id] = create_values

        # automatic logging unless asked not to (mainly for various testing purpose)
        if not self.env.context.get('mail_create_nolog'):
            threads_no_subtype = self.env[self._name]
            for thread in threads:
                subtype = thread._creation_subtype()
                if not subtype:
                    threads_no_subtype += thread
                    continue
                # if we have a subtype, post message to notify users from _message_auto_subscribe
                thread.sudo().message_post(
                    subtype_id=subtype.id, author_id=self.env.user.partner_id.id,
                    # summary="o_mail_notification" is used to hide the message body in the front-end
                    body=Markup('<div summary="o_mail_notification"><p>%s</p></div>') % thread._creation_message()
                )
            if threads_no_subtype:
                bodies = dict(
                    (thread.id, thread._creation_message())
                    for thread in threads_no_subtype)
                threads_no_subtype._message_log_batch(bodies=bodies)

        # post track template if a tracked field changed
        threads._track_discard()
        if not self.env.context.get('mail_notrack'):
            fnames = self._track_get_fields()
            for thread in threads:
                create_values = create_values_list[thread.id]
                changes = [fname for fname in fnames if create_values.get(fname)]
                # based on tracked field to stay consistent with write
                # we don't consider that a falsy field is a change, to stay consistent with previous implementation,
                # but we may want to change that behaviour later.
                if changes:
                    self.env.cr.precommit.add(thread._track_post_template_finalize)  # call to _track_post_template_finalize bound to this record
                    self.env.cr.precommit.data.setdefault(f'mail.tracking.create.{self._name}.{thread.id}', changes)
        return threads