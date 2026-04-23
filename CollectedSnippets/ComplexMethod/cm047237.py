def create(self, vals_list):
        users = super().create(vals_list)
        setting_vals = []
        for user in users:
            if not user.res_users_settings_ids and user._is_internal():
                setting_vals.append({'user_id': user.id})
            # if partner is global we keep it that way
            if user.partner_id.company_id:
                user.partner_id.company_id = user.company_id
            user.partner_id.active = user.active
            # Generate employee initals as avatar for internal users without image
            if not user.image_1920 and not user.share and user.name:
                user.image_1920 = user.partner_id._avatar_generate_svg()
        if setting_vals:
            self.env['res.users.settings'].sudo().create(setting_vals)
        return users