def _sync_cron(self):
        """ Synchronise the related cron fields to reflect this alert """
        for alert in self:
            alert = alert.with_context(tz=alert.tz)

            cron_required = (
                alert.active
                and alert.mode == 'chat'
                and (not alert.until or fields.Date.context_today(alert) <= alert.until)
            )

            sendat_tz = pytz.timezone(alert.tz).localize(datetime.combine(
                fields.Date.context_today(alert, fields.Datetime.now()),
                float_to_time(alert.notification_time, alert.notification_moment)))
            cron = alert.cron_id.sudo()
            lc = cron.lastcall
            if ((
                lc and sendat_tz.date() <= fields.Datetime.context_timestamp(alert, lc).date()
            ) or (
                not lc and sendat_tz <= fields.Datetime.context_timestamp(alert, fields.Datetime.now())
            )):
                sendat_tz += timedelta(days=1)
            sendat_utc = sendat_tz.astimezone(pytz.UTC).replace(tzinfo=None)

            cron.name = f"Lunch: alert chat notification ({alert.name})"
            cron.active = cron_required
            cron.nextcall = sendat_utc
            cron.code = dedent(f"""\
                # This cron is dynamically controlled by {self._description}.
                # Do NOT modify this cron, modify the related record instead.
                env['{self._name}'].browse([{alert.id}])._notify_chat()""")