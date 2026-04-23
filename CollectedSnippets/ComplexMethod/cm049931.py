def write(self, vals):
        for channel_member in self:
            for field_name in ['channel_id', 'partner_id', 'guest_id']:
                if field_name in vals and vals[field_name] != channel_member[field_name].id:
                    raise AccessError(_('You can not write on %(field_name)s.', field_name=field_name))

        def get_field_name(field_description):
            if isinstance(field_description, Store.Attr):
                return field_description.field_name
            return field_description

        def get_vals(member):
            return {
                get_field_name(field_description): (
                    member[get_field_name(field_description)],
                    field_description,
                )
                for field_description in self._sync_field_names()
            }

        old_vals_by_member = {member: get_vals(member) for member in self}
        result = super().write(vals)
        for member in self:
            new_values = get_vals(member)
            diff = []
            for field_name, (new_value, field_description) in new_values.items():
                old_value = old_vals_by_member[member][field_name][0]
                if new_value != old_value:
                    diff.append(field_description)
            if diff:
                diff.extend(
                    [
                        Store.One("channel_id", [], as_thread=True),
                        *self.env["discuss.channel.member"]._to_store_persona([]),
                    ]
                )
                if "message_unread_counter" in diff:
                    # sudo: bus.bus: reading non-sensitive last id
                    bus_last_id = self.env["bus.bus"].sudo()._bus_last_id()
                    diff.append({"message_unread_counter_bus_id": bus_last_id})
                Store(bus_channel=member._bus_channel()).add(member, diff).bus_send()
        return result