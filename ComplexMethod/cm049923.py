def action_notify(self):
        classified = self._classify_by_model()
        for model, activity_data in classified.items():
            records_sudo = self.env[model].sudo().browse(activity_data['record_ids'])
            activity_data['record_ids'] = records_sudo.exists().ids  # in case record was cascade-deleted in DB, skipping unlink override

        for activity in self.filtered('res_model'):
            if activity.res_id not in classified[activity.res_model]['record_ids']:
                continue

            if activity.user_id.lang:
                # Send the notification in the assigned user's language
                activity = activity.with_context(lang=activity.user_id.lang)

            model_description = activity.env['ir.model']._get(activity.res_model).display_name
            body = activity.env['ir.qweb']._render(
                'mail.message_activity_assigned',
                {
                    'activity': activity,
                    'model_description': model_description,
                    'is_html_empty': is_html_empty,
                },
                minimal_qcontext=True
            )
            record = activity.env[activity.res_model].browse(activity.res_id)
            if activity.user_id:
                record.message_notify(
                    partner_ids=activity.user_id.partner_id.ids,
                    body=body,
                    model_description=model_description,
                    email_layout_xmlid='mail.mail_notification_layout',
                    subject=_('"%(activity_name)s: %(summary)s" assigned to you',
                              activity_name=activity.res_name,
                              summary=activity.summary or activity.activity_type_id.name or ''),
                    subtitles=[_('Activity: %s', activity.activity_type_id.name or _('Todo')),
                               _('Deadline: %s', activity.date_deadline.strftime(get_lang(activity.env).date_format))],
                )