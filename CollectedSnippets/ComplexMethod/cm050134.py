def _update_subscription_from_email(self, email, opt_out=True, force_message=None):
        """ When opting-out: we have to switch opted-in subscriptions. We don't
        need to create subscription for other lists as opt-out = not being a
        member.

        When opting-in: we have to switch opted-out subscriptions and create
        subscription for other mailing lists id they are public. Indeed a
        contact is opted-in when being subscribed in a mailing list.

        :param str email: email address that should opt-in or opt-out from
          mailing lists;
        :param boolean opt_out: if True, opt-out from lists given by self if
          'email' is member of it. If False, opt-in in lists givben by self
          and create membership if not already member;
        :param str force_message: if given, post a note using that body on
          contact instead of generated update message. Give False to entirely
          skip the note step;
        """
        email_normalized = tools.email_normalize(email)
        if not self or not email_normalized:
            return

        contacts = self.env['mailing.contact'].with_context(active_test=False).search(
            [('email_normalized', '=', email_normalized)]
        )
        if not contacts:
            return

        # switch opted-in subscriptions
        if opt_out:
            current_opt_in = contacts.subscription_ids.filtered(
                lambda sub: not sub.opt_out and sub.list_id in self
            )
            if current_opt_in:
                current_opt_in.write({'opt_out': True})
        # switch opted-out subscription and create missing subscriptions
        else:
            subscriptions = contacts.subscription_ids.filtered(lambda sub: sub.list_id in self)
            current_opt_out = subscriptions.filtered('opt_out')
            if current_opt_out:
                current_opt_out.write({'opt_out': False})

            # create a subscription (for a single contact) for missing lists
            missing_lists = self - subscriptions.list_id
            if missing_lists:
                self.env['mailing.subscription'].create([
                    {'contact_id': contacts[0].id,
                     'list_id': mailing_list.id}
                    for mailing_list in missing_lists
                ])

        for contact in contacts:
            # do not log if no opt-out / opt-in was actually done
            if opt_out:
                updated = current_opt_in.filtered(lambda sub: sub.contact_id == contact).list_id
            else:
                updated = current_opt_out.filtered(lambda sub: sub.contact_id == contact).list_id + missing_lists
            if not updated:
                continue

            if force_message is False:
                continue
            if force_message:
                body = force_message
            elif opt_out:
                body = Markup('<p>%s</p><ul>%s</ul>') % (
                    _('%(contact_name)s unsubscribed from the following mailing list(s)', contact_name=contact.display_name),
                    Markup().join(Markup('<li>%s</li>') % name for name in updated.mapped('name')),
                )
            else:
                body = Markup('<p>%s</p><ul>%s</ul>') % (
                    _('%(contact_name)s subscribed to the following mailing list(s)', contact_name=contact.display_name),
                    Markup().join(Markup('<li>%s</li>') % name for name in updated.mapped('name')),
                )
            contact.with_context(mail_post_autofollow_author_skip=True).message_post(
                body=body,
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
            )