def _get_badge_user_stats(self):
        """Return stats related to badge users"""
        first_month_day = date.today().replace(day=1)

        for badge in self:
            owners = badge.owner_ids
            badge.stat_my = sum(o.user_id == self.env.user for o in owners)
            badge.stat_this_month = sum(o.create_date.date() >= first_month_day for o in owners)
            badge.stat_my_this_month = sum(
                o.user_id == self.env.user and o.create_date.date() >= first_month_day
                for o in owners
            )
            badge.stat_my_monthly_sending = sum(
                o.create_uid == self.env.user and o.create_date.date() >= first_month_day
                for o in owners
            )