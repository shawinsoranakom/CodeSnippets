def create(self, vals_list):
        for vals in vals_list:
            # find partners to add from partner_ids
            partner_ids_cmd = vals.get('channel_partner_ids') or []
            if any(cmd[0] not in (4, 6) for cmd in partner_ids_cmd):
                raise ValidationError(_('Invalid value when creating a channel with members, only 4 or 6 are allowed.'))
            partner_ids = [cmd[1] for cmd in partner_ids_cmd if cmd[0] == 4]
            partner_ids += [cmd[2] for cmd in partner_ids_cmd if cmd[0] == 6]

            # find partners to add from channel_member_ids
            membership_ids_cmd = vals.get('channel_member_ids', [])
            for cmd in membership_ids_cmd:
                if cmd[0] != 0:
                    raise ValidationError(_('Invalid value when creating a channel with memberships, only 0 is allowed.'))
                for field_name in cmd[2]:
                    if field_name not in self._get_allowed_channel_member_create_params():
                        raise ValidationError(
                            _(
                                "Invalid field “%(field_name)s” when creating a channel with members.",
                                field_name=field_name,
                            )
                        )
            membership_pids = [
                cmd[2]["partner_id"]
                for cmd in membership_ids_cmd
                if cmd[0] == 0 and "partner_id" in cmd[2]
            ]

            partner_ids_to_add = partner_ids
            # always add current user to new channel to have right values for
            # is_pinned + ensure they have rights to see channel
            if not self.env.context.get('install_mode') and not self.env.user._is_public():
                partner_ids_to_add = list(set(partner_ids + [self.env.user.partner_id.id]))
            vals['channel_member_ids'] = membership_ids_cmd + [
                (0, 0, {'partner_id': pid})
                for pid in partner_ids_to_add if pid not in membership_pids
            ]

            # clean vals
            vals.pop('channel_partner_ids', False)

        # Create channel and alias
        channels = super(DiscussChannel, self.with_context(mail_create_bypass_create_check=self.env['discuss.channel.member']._bypass_create_check, mail_create_nolog=True, mail_create_nosubscribe=True)).create(vals_list)
        # pop the mail_create_bypass_create_check key to avoid leaking it outside of create)
        channels = channels.with_context(mail_create_bypass_create_check=None)
        channels._subscribe_users_automatically()
        if not self.env.context.get("install_mode") and not self.env.user._is_public():
            Store(bus_channel=self.env.user).add(channels).bus_send()
        return channels