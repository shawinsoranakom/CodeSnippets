def _response_discuss_channel_invitation(self, store, channel, guest_email=None):
        # group restriction takes precedence over token
        # sudo - res.groups: can access group public id of parent channel to determine if we
        # can access the channel.
        group_public_id = channel.group_public_id or channel.parent_channel_id.sudo().group_public_id
        if group_public_id and group_public_id not in request.env.user.all_group_ids:
            raise request.not_found()
        guest_already_known = channel.env["mail.guest"]._get_guest_from_context()
        with replace_exceptions(UserError, by=NotFound()):
            # sudo: mail.guest - creating a guest and its member inside a channel of which they have the token
            __, guest = channel.sudo()._find_or_create_persona_for_channel(
                guest_name=guest_email if guest_email else _("Guest"),
                country_code=request.geoip.country_code,
                timezone=request.env["mail.guest"]._get_timezone_from_request(request),
            )
        if guest_email and not guest.email:
            # sudo - mail.guest: writing email address of self guest is allowed
            guest.sudo().email = guest_email
        if guest and not guest_already_known:
            store.add_global_values(is_welcome_page_displayed=True)
            channel = channel.with_context(guest=guest)
        return self._response_discuss_public_template(store, channel)