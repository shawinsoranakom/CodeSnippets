def create(self, vals_list):
        # fill missing old value with current user karma
        users = self.env['res.users'].browse([
            values['user_id']
            for values in vals_list
            if 'old_value' not in values and values.get('user_id')
        ])
        karma_per_users = {user.id: user.karma for user in users}

        for values in vals_list:
            if 'old_value' not in values and values.get('user_id'):
                values['old_value'] = karma_per_users[values['user_id']]

            if 'gain' in values and 'old_value' in values:
                values['new_value'] = values['old_value'] + values['gain']
                del values['gain']

        return super().create(vals_list)