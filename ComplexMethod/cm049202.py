def _odoo_reminders_commands_m(self, microsoft_event):
        reminders_commands = []
        if microsoft_event.isReminderOn:
            event_id = self.browse(microsoft_event.odoo_id(self.env))
            alarm_type_label = _("Notification")

            minutes = microsoft_event.reminderMinutesBeforeStart or 0
            alarm = self.env['calendar.alarm'].search([
                ('alarm_type', '=', 'notification'),
                ('duration_minutes', '=', minutes)
            ], limit=1)
            if alarm and alarm not in event_id.alarm_ids:
                reminders_commands = [(4, alarm.id)]
            elif not alarm:
                if minutes == 0:
                    interval = 'minutes'
                    duration = minutes
                    name = _("%s - At time of event", alarm_type_label)
                elif minutes % (60*24) == 0:
                    interval = 'days'
                    duration = minutes / 60 / 24
                    name = _(
                        "%(reminder_type)s - %(duration)s Days",
                        reminder_type=alarm_type_label,
                        duration=duration,
                    )
                elif minutes % 60 == 0:
                    interval = 'hours'
                    duration = minutes / 60
                    name = _(
                        "%(reminder_type)s - %(duration)s Hours",
                        reminder_type=alarm_type_label,
                        duration=duration,
                    )
                else:
                    interval = 'minutes'
                    duration = minutes
                    name = _(
                        "%(reminder_type)s - %(duration)s Minutes",
                        reminder_type=alarm_type_label,
                        duration=duration,
                    )
                reminders_commands = [(0, 0, {'duration': duration, 'interval': interval, 'name': name, 'alarm_type': 'notification'})]

            alarm_to_rm = event_id.alarm_ids.filtered(lambda a: a.alarm_type == 'notification' and a.id != alarm.id)
            if alarm_to_rm:
                reminders_commands += [(3, a.id) for a in alarm_to_rm]

        else:
            event_id = self.browse(microsoft_event.odoo_id(self.env))
            alarm_to_rm = event_id.alarm_ids.filtered(lambda a: a.alarm_type == 'notification')
            if alarm_to_rm:
                reminders_commands = [(3, a.id) for a in alarm_to_rm]
        return reminders_commands