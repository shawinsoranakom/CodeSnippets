def _notify_get_classified_recipients_iterator(
            self, message, recipients_data, msg_vals=False,
            model_description=False, force_email_company=False, force_email_lang=False,  # rendering
            force_record_name=False,  # rendering
            subtitles=None):
        """ Make groups of recipients, based on 'recipients_data' which is a list
        of recipients informations. Purpose of this method is to group them by
        main usage ('user', 'portal_user', 'follower', 'customer', ... see
        @_notify_get_recipients_classify) and lang. Each group is linked to
        an evaluation context to render the notification layout.

        :param message: ``mail.message`` record to notify;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like a list of dicts containing information. See
          ``MailThread._notify_get_recipients()``;
        :param msg_vals: dictionary of values used to create the message. If
          given it may be used to access values related to ``message``;

        :param str model_description: description of current model, given to
          avoid fetching it and easing translation support;
        :param record force_email_company: <res.company> record used when rendering
          notification layout. Otherwise computed based on current record;
        :param str force_email_lang: when no specific lang is found this is the
          default lang to use notably to compute model name or translate access
          buttons;
        :param str force_record_name: record_name to use instead of being
          related record's display_name;
        :param list subtitles: optional list set as template value "subtitles";

        :return: iterator based on recipients classified by lang, with their
          rendering evaluation context. Each item is a tuple containing (
            lang: used for rendering (customer language, forced email, default
              environment language,
            render_values: used to render the notification layout and translated
              using lang,
            recipients_group: a recipients group is a dict containing data
              defined in "_notify_get_recipients_groups" like {
              'active': if not, it is skipped in notification process (ease
                        inheritance to be already present);
              'button_access': main access document button information, {'url'
                               link of the access, 'title': link or button
                               string};
              'has_button_access': display access document main button in email;
              'notification_group_name': name of the group, to ease usage;
              'recipients_data': list of recipients data, following format used
                                 in '_notify_get_recipients'. It is fillup when
                                 evaluating groups;
              'recipients_ids': list of partner IDs, based on partner ID present in
                                recipients_data (allows mainly to speedup some
                                data computation);
              'recipients_emails': list of additional external emails, when not
                                   linked to existing partners. Support is still
                                   limited and considered as experimental as of v19;
           }
          );
        """
        lang_to_recipients = {}
        for data in recipients_data:
            # filter active lang
            if lang_code := data.get('lang'):
                lang_code = bool(self.env['res.lang']._lang_get(lang_code)) and lang_code
            lang_to_recipients.setdefault(
                lang_code or force_email_lang or self.env.lang,
                [],
            ).append(data)

        for lang, lang_recipients_data in lang_to_recipients.items():
            record_wlang = self.with_context(lang=lang)
            lang_model_description = model_description
            if not lang_model_description:
                lang_model_description = record_wlang._get_model_description(msg_vals and msg_vals.get('model') or message.model)
            recipients_groups_list = record_wlang._notify_get_recipients_classify(
                message,
                lang_recipients_data,
                lang_model_description,
                msg_vals=msg_vals,
            )
            render_values = record_wlang._notify_by_email_prepare_rendering_context(
                message,
                msg_vals=msg_vals,
                model_description=lang_model_description,
                force_email_company=force_email_company,
                force_email_lang=lang,
                force_record_name=force_record_name,
            ) # 10 queries
            if subtitles:
                render_values['subtitles'] = subtitles

            for recipients_group in recipients_groups_list:
                if not render_values['show_unfollow']:
                    render_values['show_unfollow'] = any(
                        r['is_follower']
                        for r in recipients_group['recipients_data']
                        if r['id'] and r['uid'] and not r['ushare']
                    )
                yield (lang, render_values, recipients_group)