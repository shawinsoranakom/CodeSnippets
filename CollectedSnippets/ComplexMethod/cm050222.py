def save_edited_profile(self, **kwargs):
        user_id = int(kwargs.get('user_id', 0))
        if user_id and request.env.user.id != user_id and request.env.user._is_admin():
            user = request.env['res.users'].browse(user_id)
        else:
            user = request.env.user
        values = self._profile_edition_preprocess_values(user, **kwargs)
        whitelisted_values = {key: values[key] for key in sorted(user._self_accessible_fields()[1]) if key in values}
        if not user.partner_id._can_edit_country() and whitelisted_values.get('country_id') != user.partner_id.country_id.id:
            raise UserError(_("Changing the country is not allowed once document(s) have been issued for your account. Please contact us directly for this operation."))
        user.write(whitelisted_values)