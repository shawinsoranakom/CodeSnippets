def _notify_get_recipients_classify(self, message, recipients_data,
                                        model_description, msg_vals=False):
        """ Classify recipients to be notified of a message in groups to have
        specific rendering depending on their group. For example users could
        have access to buttons customers should not have in their emails.
        Module-specific grouping should be done by overriding ``_notify_get_recipients_groups``
        method defined here-under.

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like a list of dicts containing information. See
          ``MailThread._notify_get_recipients()``;
        :param str model_description: description of current model, given to
          avoid fetching it and easing translation support;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries if given;

        :return: list of groups (see '_notify_get_recipients_groups')
          with 'recipients' key filled with matching partners, like
            [{
                'active': True,
                'button_access': {'url': 'https://odoo.com/url', 'title': 'Title'},
                'has_button_access': False,
                'notification_group_name': 'user',
                'recipients_data': [{...}],
                'recipients_ids': [11],
             }, {...}]
        :rtype: list[dict]
        """
        # keep a local copy of msg_vals as it may be modified to include more
        # information about groups or links
        local_msg_vals = dict(msg_vals) if msg_vals else {}
        groups = self._notify_get_recipients_groups_fillup(
            self._notify_get_recipients_groups(
                message, model_description, msg_vals=local_msg_vals
            ),
            model_description,
            msg_vals=local_msg_vals
        )
        # sanitize groups
        for _group_name, _group_func, group_data in groups:
            if 'actions' in group_data:
                _logger.warning('Invalid usage of actions in notification groups')

        # classify recipients in each group
        for recipient_data in recipients_data:
            for _group_name, group_func, group_data in groups:
                if group_data['active'] and group_func(recipient_data):
                    group_data['recipients_data'].append(recipient_data)
                    if recipient_data['id']:
                        group_data['recipients_ids'].append(recipient_data['id'])
                    elif recipient_data['email_normalized']:
                        group_data['recipients_emails'].append(recipient_data['email_normalized'])
                    break

        # filter out groups without recipients
        return [
            group_data
            for _group_name, _group_func, group_data in groups
            if group_data['recipients_data']
        ]