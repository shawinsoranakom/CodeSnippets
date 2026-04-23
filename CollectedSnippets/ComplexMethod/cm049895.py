def _notify_by_email_prepare_rendering_context(self, message, msg_vals=False,
                                                   model_description=False,
                                                   force_email_company=False,
                                                   force_email_lang=False,
                                                   force_record_name=False):
        """ Prepare rendering context for notification email.

        Signature: if asked a default signature is computed based on author. Either
        it has an user and we use the user's signature. Either we do not find any
        user and we compute a default one based on the author's name.

        Company: either there is one defined on the record (company_id field set
        with a value), either we use env.company. A new parameter allows to force
        its value.

        Lang: when calling this method, ``_fallback_lang`` should already been
        called, or a lang set in context with another way. A wild guess is done
        based on templates to try to retrieve the recipient's language when a flow
        like "send by email" is performed. Lang is used to try to have the
        notification layout in the same language as the email content. A new
        parameter allows to force its value.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries if given;
        :param str model_description: description of current model, given to
          avoid fetching it and easing translation support;
        :param record force_email_company: <res.company> record used when rendering
          notification layout. Otherwise computed based on current record;
        :param str force_email_lang: lang used when rendering content, used
          notably to compute model name or translate access buttons;
        :param str force_record_name: record_name to use instead of being
          related record's display_name;

        :return: dictionary of values used when rendering notification layout;
        """
        msg_vals = msg_vals or {}

        lang = force_email_lang if force_email_lang else self.env.lang
        record_wlang = self.with_context(lang=lang)

        author = message.env['res.partner'].browse(msg_vals.get('author_id')) if 'author_id' in msg_vals else message.author_id
        author_user = author.main_user_id
        signature, email_add_signature = '', False

        if author_user:
            email_add_signature = msg_vals.get('email_add_signature', message.email_add_signature)
            if email_add_signature:
                signature = Markup('<div>-- <br/>%s</div>') % author_user.signature

        if force_email_company:
            company = force_email_company
        else:
            company = record_wlang.company_id.sudo() if (
                record_wlang and 'company_id' in record_wlang and record_wlang.company_id
            ) else record_wlang.env.company
        if company.website:
            website_url = 'http://%s' % company.website if not company.website.lower().startswith(('http:', 'https:')) else company.website
        else:
            website_url = False

        # record, model
        if not model_description:
            model_description = record_wlang._get_model_description(msg_vals['model'] if 'model' in msg_vals else message.model)
        record_name = force_record_name or message.with_context(lang=lang).record_name

        # tracking: in case of missing value, perform search (skip only if sure we don't have any)
        check_tracking = msg_vals.get('tracking_value_ids', True) if msg_vals else bool(self)
        tracking = []
        if check_tracking:
            tracking_values = self.env['mail.tracking.value'].sudo().search(
                [('mail_message_id', 'in', message.ids)]
            )._filter_has_field_access(self.env)
            if tracking_values and hasattr(record_wlang, '_track_filter_for_display'):
                tracking_values = record_wlang._track_filter_for_display(tracking_values)
            tracking = [
                (
                    fmt_vals['fieldInfo']['changedField'],
                    fmt_vals['oldValue'],
                    fmt_vals['newValue'],
                ) for fmt_vals in tracking_values._tracking_value_format()
            ]

        subtype_id = msg_vals['subtype_id'] if 'subtype_id' in msg_vals else message.subtype_id.id
        is_discussion = subtype_id == self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')

        return {
            # message
            'is_discussion': is_discussion,
            'message': message,
            'subtype': message.subtype_id,
            'tracking_values': tracking,
            # record
            'model_description': model_description,
            'record': record_wlang,
            'record_name': record_name,
            'subtitles': [record_name],
            # user / environment
            'author_user': author_user,  # User who sends the message
            'company': company,
            'email_add_signature': email_add_signature,
            'lang': lang,
            'show_unfollow': getattr(self, '_partner_unfollow_enabled', False),
            'signature': signature,
            'website_url': website_url,
            # tools
            'is_html_empty': is_html_empty,
            # display
            'email_notification_force_header': self.env.context.get('email_notification_force_header', False),  # force displaying the email header
            'email_notification_force_footer': self.env.context.get('email_notification_force_footer', False),  # force displaying the email footer
            'email_notification_allow_header': self.env.context.get('email_notification_allow_header', True),
            'email_notification_allow_footer': self.env.context.get('email_notification_allow_footer', False),
        }