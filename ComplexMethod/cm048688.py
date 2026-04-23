def message_new(self, msg_dict, custom_values=None):
        # EXTENDS mail mail.thread
        custom_values = custom_values or {}
        # Add custom behavior when receiving a new invoice through the mail's gateway.
        if custom_values.get('move_type', 'entry') not in ('out_invoice', 'in_invoice', 'entry'):
            return super().message_new(msg_dict, custom_values=custom_values)

        self = self.with_context(skip_is_manually_modified=True)  # noqa: PLW0642

        company = self.env['res.company'].browse(custom_values['company_id']) if custom_values.get('company_id') else self.env.company

        def is_internal_partner(partner):
            # Helper to know if the partner is an internal one.
            return (
                    company.partner_id in (partner | partner.parent_id)
                    or (partner.user_ids and all(user._is_internal() for user in partner.user_ids))
            )

        def filter_found(partner):
            return not company or partner.company_id.id in [False, company.id] or partner.partner_share

        # Search for partner that sent the mail.
        from_mail_addresses = email_split(msg_dict.get('from', ''))
        partners = self._partner_find_from_emails_single(from_mail_addresses, filter_found=filter_found, no_create=True)
        # if we are in the case when an internal user forwarded the mail manually
        # search for partners in mail's body
        if partners and is_internal_partner(partners[0]) and (body_mail_addresses := set(email_re.findall(msg_dict.get('body') or ''))):
            # Search for partners in the mail's body.
            partners = self._partner_find_from_emails_single(body_mail_addresses, filter_found=filter_found, no_create=True)

        # Never return an internal partner
        partners = partners.filtered(lambda p: not is_internal_partner(p))

        # Little hack: Inject the mail's subject in the body.
        if msg_dict.get('subject') and msg_dict.get('body'):
            msg_dict['body'] = Markup('<div><div><h3>%s</h3></div>%s</div>') % (msg_dict['subject'], msg_dict['body'])

        # Create the invoice.
        values = {
            'name': '/',  # we have to give the name otherwise it will be set to the mail's subject
            'invoice_source_email': from_mail_addresses[0],
            'partner_id': partners[0].id if partners else False,
        }
        move_ctx = self.with_context(
            from_alias=True,
            default_move_type=custom_values.get('move_type', 'entry'),
            default_journal_id=custom_values.get('journal_id'),
            default_company_id=company.id,
        )
        move = super(AccountMove, move_ctx).message_new(msg_dict, custom_values=values)
        move._compute_name()  # because the name is given, we need to recompute in case it is the first invoice of the journal

        return move