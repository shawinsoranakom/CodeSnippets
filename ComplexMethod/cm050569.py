def _get_channel_values_from_invite(channel_id, invite_hash, invite_partner_id):
        """ Check identification parameters and returns values used to give access to signed out invited members.
        The course is returned as sudo to allow them seeing a preview of the course even if visibility if not public.
        Returns dict of values or containing 'invite_error' and a value corresponding to the error. See _get_invite_error_msg."""
        channel_sudo = request.env['slide.channel'].browse(channel_id).exists().sudo()
        partner_sudo = request.env['res.partner'].browse(invite_partner_id).exists().sudo()
        if not partner_sudo or not channel_sudo.is_published:
            return {'invite_error': 'no_partner' if not partner_sudo else 'no_channel' if not channel_sudo else 'no_rights'}

        channel_partner_sudo = channel_sudo.channel_partner_all_ids.filtered(lambda cp: cp.partner_id.id == invite_partner_id)
        if not channel_partner_sudo:
            return {'invite_error': 'expired'}
        if not consteq(channel_partner_sudo._get_invitation_hash(), invite_hash):
            return {'invite_error': 'hash_fail'}

        if channel_partner_sudo.member_status == 'invited':
            if not channel_partner_sudo.last_invitation_date or \
               channel_partner_sudo.last_invitation_date + relativedelta(months=3) < fields.Datetime.now():
                return {'invite_error': 'expired'}

        return {
            'invite_channel': channel_sudo,
            'invite_channel_partner': channel_partner_sudo,
            'invite_preview': True,
            'is_partner_without_user': not partner_sudo.user_ids,
            'invite_partner': partner_sudo
        }