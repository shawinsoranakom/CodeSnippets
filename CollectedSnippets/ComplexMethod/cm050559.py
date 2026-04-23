def _notify_chat(self):
        # Called daily by cron
        self.ensure_one()

        if not self.available_today:
            _logger.warning("cancelled, not available today")
            if self.cron_id and self.until and fields.Date.context_today(self) > self.until:
                self.cron_id.unlink()
                self.cron_id = False
            return

        if not self.active or self.mode != 'chat':
            raise ValueError("Cannot send a chat notification in the current state")

        order_domain = Domain('state', '!=', 'cancelled')

        if self.location_ids.ids:
            order_domain &= Domain('user_id.last_lunch_location_id', 'in', self.location_ids.ids)

        if self.recipients != 'everyone':
            weeksago = fields.Date.today() - timedelta(weeks=(
                1 if self.recipients == 'last_week' else
                4 if self.recipients == 'last_month' else
                52  # if self.recipients == 'last_year'
            ))
            order_domain &= Domain('date', '>=', weeksago)

        partners = self.env['lunch.order'].search(order_domain).user_id.partner_id
        if partners:
            self.env['mail.thread'].message_notify(
                model=self._name,
                res_id=self.id,
                body=self.message,
                partner_ids=partners.ids,
                subject=_('Your Lunch Order'),
            )