def _execute_action_channel(self, user_key, channel_key, membership, operation, result, for_sub_channel):
        current_user = self.users[user_key]
        guest = self.guest if user_key == "public" else self.env["mail.guest"]
        ChannelAsUser = self.env["discuss.channel"].with_user(current_user).with_context(guest=guest)
        if operation == "create":
            group_public_id = None
            if channel_key == "group_matching":
                group_public_id = self.secret_group.id
            elif channel_key == "group_failing":
                group_public_id = self.env.ref("base.group_system").id
            data = {
                "name": "Test Channel",
                "channel_type": channel_key if channel_key in ("group", "chat") else "channel",
                "group_public_id": group_public_id,
            }
            ChannelAsUser.create(data)
        else:
            channel = ChannelAsUser.browse(
                self._get_channel_id(user_key, channel_key, membership, for_sub_channel)
            )
            self.assertEqual(len(channel), 1, "should find the channel")
            if operation == "read":
                self.assertEqual(len(ChannelAsUser.search([("id", "=", channel.id)])), 1 if result else 0)
                channel.read(["name"])
            elif operation == "write":
                channel.write({"name": "new name"})
            elif operation == "unlink":
                channel.unlink()