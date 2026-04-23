def write(self, vals):
        res = super().write(vals)
        if "active" in vals and not vals["active"]:
            self._unsubscribe_from_non_public_channels()
        if vals.get("group_ids"):
            # form: {'group_ids': [(3, 10), (3, 3), (4, 10), (4, 3)]} or {'group_ids': [(6, 0, [ids]}
            user_group_ids = [command[1] for command in vals["group_ids"] if command[0] == 4]
            user_group_ids += [id for command in vals["group_ids"] if command[0] == 6 for id in command[2]]
            user_group_ids += self.env['res.groups'].browse(user_group_ids).all_implied_ids._ids
            self.env["discuss.channel"].search([("group_ids", "in", user_group_ids)])._subscribe_users_automatically()
        return res