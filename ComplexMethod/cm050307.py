def _can_grant_badge(self):
        """Check if a user can grant a badge to another user

        :return: integer representing the permission.
        """
        if self.env.is_admin():
            return self.CAN_GRANT

        if self.rule_auth == 'nobody':
            return self.NOBODY_CAN_GRANT
        elif self.rule_auth == 'users' and self.env.user not in self.rule_auth_user_ids:
            return self.USER_NOT_VIP
        elif self.rule_auth == 'having':
            all_user_badges = self.env['gamification.badge.user'].search([('user_id', '=', self.env.uid)]).mapped('badge_id')
            if self.rule_auth_badge_ids - all_user_badges:
                return self.BADGE_REQUIRED

        if self.rule_max and self.stat_my_monthly_sending >= self.rule_max_number:
            return self.TOO_MANY

        # badge.rule_auth == 'everyone' -> no check
        return self.CAN_GRANT