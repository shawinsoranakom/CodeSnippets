def write(self, vals):
        if 'channel_type' in vals:
            failing_channels = self.filtered(lambda channel: channel.channel_type != vals.get('channel_type'))
            if failing_channels:
                raise UserError(_('Cannot change the channel type of: %(channel_names)s', channel_names=', '.join(failing_channels.mapped('name'))))
        if {"from_message_id", "parent_channel_id"} & set(vals):
            raise UserError(
                _(
                    "Cannot change initial message nor parent channel of: %(channels)s.",
                    channels=self.mapped("name"),
                )
            )
        if "group_public_id" in vals:
            if failing_channels := self.filtered(lambda channel: channel.parent_channel_id):
                raise UserError(
                    self.env._(
                        "Cannot change authorized group of sub-channel: %(channels)s.",
                        channels=failing_channels.mapped("name"),
                    )
                )

        def get_field_name(field_description):
            if isinstance(field_description, Store.Attr):
                return field_description.field_name
            return field_description

        def get_field_value(channel, field_description):
            if isinstance(field_description, Store.Attr):
                if field_description.predicate and not field_description.predicate(channel):
                    return None
            if isinstance(field_description, Store.Relation):
                return field_description._get_value(channel).records
            if isinstance(field_description, Store.Attr):
                return field_description._get_value(channel)
            return channel[field_description]

        def get_vals(channel):
            return {
                subchannel: {
                    get_field_name(field_description): (
                        get_field_value(channel, field_description),
                        field_description,
                    )
                    for field_description in field_descriptions
                }
                for subchannel, field_descriptions in self._sync_field_names().items()
            }

        old_vals = {channel: get_vals(channel) for channel in self}
        result = super().write(vals)
        for channel in self:
            new_subchannel_vals = get_vals(channel)
            for subchannel, values in new_subchannel_vals.items():
                diff = []
                for field_name, (value, field_description) in values.items():
                    if value != old_vals[channel][subchannel][field_name][0]:
                        diff.append(field_description)
                if diff:
                    Store(
                        bus_channel=channel,
                        bus_subchannel=subchannel,
                    ).add(channel, diff).bus_send()
        if vals.get('group_ids'):
            self._subscribe_users_automatically()
        return result