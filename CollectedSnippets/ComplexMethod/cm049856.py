def _message_get_suggested_recipients_batch(self, reply_discussion=False, reply_message=None,
                                                no_create=True, primary_email=False, additional_partners=None):
        """ Get suggested recipients, contextualized depending on discussion.
        This method automatically filters out emails and partners linked to
        aliases or alias domains.

        :param bool reply_discussion: consider user replies to the discussion.
          Last relevant message is fetched and used to search for additional
          'To' and 'Cc' to propose;
        :param <mail.message> reply_message: specific message user is replying-to.
          Bypasses 'reply_discussion';
        :param bool no_create: do not create partners when emails are not linked
          to existing partners, see '_partner_find_from_emails';
        :param bool primary_email: new primary_email that isn't stored inside DB;
        :param bool additional_partners: partners that needs to be added to the suggested recipients;

        :returns: list of dictionaries (per suggested recipient) containing:
            * create_values:         dict: data to populate new partner, if not found
            * email:                 str: email of recipient
            * name:                  str: name of the recipient
            * partner_id:            int: recipient partner id
        """
        def email_key(email):
            return email_normalize(email, strict=False) or email.strip()
        is_mail_thread = 'message_partner_ids' in self
        suggested_record = self._message_add_suggested_recipients(force_primary_email=primary_email)

        # copy suggested based on records, then add those from context
        suggested = {}
        for record in self:
            suggested[record.id] = {
                'email_to_lst': suggested_record[record.id]['email_to_lst'].copy(),
                'partners': suggested_record[record.id]['partners'] + (additional_partners or self.env['res.partner']),
            }

        # find last relevant message
        messages = self.env['mail.message']
        if reply_discussion and 'message_ids' in self:
            messages = self._sort_suggested_messages(self.message_ids)
        # fetch answer-based recipients as well as author
        if reply_message or messages:
            for record in self:
                record_msg = reply_message or next(
                    (msg for msg in messages if msg.res_id == record.id and msg.message_type in ('comment', 'email')),
                    self.env['mail.message']
                )
                if not record_msg:
                    continue
                # direct recipients, and author if not archived / root
                suggested[record.id]['partners'] += (record_msg.partner_ids | record_msg.author_id).filtered(lambda p: p.active)
                # To and Cc emails (mainly for incoming email), and email_from if not linked to hereabove author
                suggested[record.id]['email_to_lst'] += [record_msg.incoming_email_to or '', record_msg.incoming_email_cc or '', record_msg.email_from or '']
                from_normalized = email_normalize(record_msg.email_from)
                if from_normalized and from_normalized != record_msg.author_id.email_normalized:
                    suggested[record.id]['email_to_lst'].append(record_msg.email_from)

        # make a record-based list of emails to give to '_partner_find_from_emails'
        records_emails = {}
        all_emails = set()
        for record in self:
            email_to_lst, partners = suggested[record.id]['email_to_lst'], suggested[record.id]['partners']
            # organize and deduplicate partners, exclude followers, keep ordering
            followers = record.message_partner_ids if is_mail_thread else record.env['res.partner']
            # sanitize email inputs, exclude followers and aliases, add some banned emails, keep ordering, then link to partners
            skip_emails_normalized = (followers | partners).mapped('email_normalized') + (followers | partners).mapped('email')
            records_emails[record] = [
                e for email_input in email_to_lst for e in email_split_and_format(email_input)
                if e and e.strip() and email_key(e) not in skip_emails_normalized
            ]
            all_emails |= set(records_emails[record]) | set(partners.mapped('email_normalized'))
        # ban emails: never propose odoobot nor aliases
        ban_emails = [self.env.ref('base.partner_root').email_normalized]
        ban_emails += self.env['mail.alias.domain'].sudo()._find_aliases(
            [email_key(e) for e in all_emails if e and e.strip()]
        )
        thread_recs = self if is_mail_thread else self.env['mail.thread']
        records_partners = thread_recs._partner_find_from_emails(
            records_emails,
            # already computed in ban_emails, no need to re-check aliases
            avoid_alias=False, ban_emails=ban_emails,
            no_create=no_create,
        )

        # final filtering, and fetch model-related additional information for create values
        emails_normalized_info = self._get_customer_information() if is_mail_thread else {}
        suggested_recipients = {}
        for record in self:
            followers = record.message_partner_ids if is_mail_thread else record.env['res.partner']
            partners = self.env['res.partner'].browse(tools.misc.unique(
                p.id for p in (suggested[record.id]['partners'] + records_partners[record.id])
                if (
                    # skip followers, unless being a customer suggested by record (mostly defaults)
                    (
                        p not in followers or (
                            p in suggested_record[record.id]['partners'] and
                            p.partner_share
                    )) and
                    p.email_normalized not in ban_emails and
                    not p.is_public
                )
            ))
            existing_mails = {
                email_key(e)
                for rec in (followers | partners)
                for e in ([rec.email_normalized] if rec.email_normalized else []) + email_split_and_format(rec.email or '')
            }
            email_to_lst = list(tools.misc.unique(
                e for email_input in suggested[record.id]['email_to_lst'] for e in email_split_and_format(email_input)
                if (
                    e and e.strip() and
                    email_key(e) not in ban_emails and
                    email_key(e) not in existing_mails
                )
            ))

            recipients = [{
                **({'display_name': partner.display_name} if not partner.name else {}),
                'email': partner.email_normalized,
                'name': partner.name,
                'partner_id': partner.id,
                'create_values': {},
            } for partner in partners]
            for email_input in email_to_lst:
                name, email_normalized = parse_contact_from_email(email_input)
                recipients.append({
                    'email': email_normalized,
                    'name': emails_normalized_info.get(email_normalized, {}).pop('name', False) or name,
                    'partner_id': False,
                    'create_values': emails_normalized_info.get(email_normalized, {}),
                })
            suggested_recipients[record.id] = recipients
        return suggested_recipients