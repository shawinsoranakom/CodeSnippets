def _compute_date_to(self):
        user_tz = self.env.tz
        if not (self.env.user.tz or self.env.context.get('tz')):
            user_tz = timezone(self.company_id.resource_calendar_id.tz or 'UTC')
        for leave in self:
            if not leave.date_from or (leave.date_to and leave.date_to > leave.date_from):
                continue
            local_date_from = utc.localize(leave.date_from).astimezone(user_tz)
            local_date_to = local_date_from + relativedelta(hour=23, minute=59, second=59)
            leave.date_to = local_date_to.astimezone(utc).replace(tzinfo=None)