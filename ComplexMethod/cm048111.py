def _notify_records_to_recycle(self):
        for recycle in self.search([('recycle_mode', '=', 'manual')]):
            if not recycle.notify_user_ids or not recycle.notify_frequency:
                continue

            if recycle.notify_frequency_period == 'days':
                delta = relativedelta(days=recycle.notify_frequency)
            elif recycle.notify_frequency_period == 'weeks':
                delta = relativedelta(weeks=recycle.notify_frequency)
            else:
                delta = relativedelta(months=recycle.notify_frequency)

            if not recycle.last_notification or\
                    (recycle.last_notification + delta) < fields.Datetime.now():
                recycle.last_notification = fields.Datetime.now()
                recycle._send_notification(delta)