def _send_notifications(self, default_notify_kwargs=None):
        """ Send notification for scheduled messages.

        :param dict default_notify_kwargs: optional parameters to propagate to
          ``notify_thread``. Those are default values overridden by content of
          ``notification_parameters`` field.
        """
        for model, schedules in self._group_by_model().items():
            if model:
                records = self.env[model].browse(schedules.mapped('mail_message_id.res_id'))
                existing = records.exists()
            else:
                records = [self.env['mail.thread']] * len(schedules)
                existing = records

            for record, schedule in zip(records, schedules):
                if record not in existing:
                    continue
                notify_kwargs = dict(default_notify_kwargs or {}, skip_existing=True)
                try:
                    schedule_notify_kwargs = json.loads(schedule.notification_parameters)
                except Exception:
                    pass
                else:
                    schedule_notify_kwargs.pop('scheduled_date', None)
                    notify_kwargs.update(schedule_notify_kwargs)

                record._notify_thread(schedule.mail_message_id, msg_vals=False, **notify_kwargs)

        self.unlink()
        return True