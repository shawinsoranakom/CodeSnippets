def write(self, vals):
        if user_domain := vals.get('user_domain'):
            users = self._get_challenger_users(str(user_domain))

            if not vals.get('user_ids'):
                vals['user_ids'] = []
            vals['user_ids'].extend((4, user.id) for user in users)

        write_res = super().write(vals)

        if vals.get('state') == 'inprogress':
            self._recompute_challenge_users()
            self._generate_goals_from_challenge()

        elif vals.get('state') == 'done':
            self._check_challenge_reward(force=True)

        elif vals.get('state') == 'draft':
            # resetting progress
            if self.env['gamification.goal'].search_count([('challenge_id', 'in', self.ids), ('state', '=', 'inprogress')], limit=1):
                raise exceptions.UserError(_("You can not reset a challenge with unfinished goals."))

        return write_res