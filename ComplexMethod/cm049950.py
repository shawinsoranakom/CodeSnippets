def is_internal(self, env):
            """Return whether the current target implies the information will only be sent to
            internal users. If there is no target at all, the check is based on the current
            user of the env."""
            bus_record = self.channel
            if bus_record is None and self.subchannel is None:
                bus_record = env.user
            return (
                (
                    isinstance(bus_record, env.registry["res.users"])
                    and self.subchannel is None
                    and bus_record._is_internal()
                )
                or (
                    isinstance(bus_record, env.registry["discuss.channel"])
                    and (
                        self.subchannel == "internal_users"
                        or (
                            bus_record.channel_type == "channel"
                            and env.ref("base.group_user")
                            in bus_record.group_public_id.all_implied_ids
                        )
                    )
                )
                or (
                    isinstance(self.channel, env.registry["res.groups"])
                    and env.ref("base.group_user") in self.channel.implied_ids
                )
            )