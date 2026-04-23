def slide_channel_invite(self, channel_id, invite_partner_id, invite_hash):
        """ This route is included in the invitation link in email to join / check out the course. It is
        the main entry point on the attendee's side when sharing or inviting them. As rule of thumb, this will
        redirect to the course if the rights are given, and to the main /slides page with appropriate error
        message otherwise. (See _get_invite_error_msg method)

        It acts as a redirector:
            - Returns error if parameters are not valid or if expired invitation.
            - If a user is logged, verify the link is for this user. Redirects according to Acl's.
            - If no user is logged:
                - Redirects to login / signup if the partner is enrolled.
                - Redirects to the course with invite parameters. They will be able to browse a course preview
                before logging in / signing up, as prompted in an information banner.

        :param channel_id: The id of the course the user is invited to. Do not use <model> in the route instead,
            otherwise an error 403 could be returned if the (public) user has no access to the record.
        :param invite_partner_id: The id of the invited partner.
        :param invite_hash: The invitation hash that allows a direct access to channel_id, even if not connected.
        """
        channel = request.env['slide.channel'].browse(int(channel_id)).exists()
        if not channel:
            return self._redirect_to_slides_main('no_channel')

        # --- Compute rights of current user
        has_rights = channel.has_access('read')

        invite_values = self._get_channel_values_from_invite(channel_id, invite_hash, int(invite_partner_id))
        if invite_values.get('invite_error'):
            return self._redirect_to_channel(channel) if has_rights else self._redirect_to_slides_main(invite_values.get('invite_error'))

        invite_partner = invite_values.get('invite_partner')
        invite_channel_partner = invite_values.get('invite_channel_partner')

        # --- A user is logged
        if not request.website.is_public_user():
            if request.env.user.partner_id.id != invite_partner.id:
                return self._redirect_to_slides_main('partner_fail')
            return self._redirect_to_channel(channel) if has_rights else self._redirect_to_slides_main('no_rights')

        redirect_url = f'/slides/{channel_id}'

        # --- No user is logged.
        if invite_channel_partner.member_status != 'invited':
            # Enrolled partner. Access to the course but needs to log in / sign up.
            if invite_values.get('is_partner_without_user'):
                invite_partner.signup_prepare()
                signup_url = invite_partner._get_signup_url_for_action(url=redirect_url)[invite_partner.id]
                return request.redirect(signup_url)
            else:
                return request.redirect(f'/web/login?redirect={redirect_url}&auth_login={invite_partner.user_ids[0].login}')
        # Pending invitation. A banner will allow partner to login / signup on the course page.
        return request.redirect(f'{redirect_url}?invite_partner_id={invite_partner_id}&invite_hash={invite_hash}')