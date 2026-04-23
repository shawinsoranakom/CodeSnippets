def _execute_action_member(self, channel_id, user_key, target, operation, result):
        current_user = self.users[user_key]
        partner = self.env["res.partner"] if user_key == "public" else current_user.partner_id
        guest = self.guest if user_key == "public" else self.env["mail.guest"]
        ChannelMemberAsUser = self.env["discuss.channel.member"].with_user(current_user).with_context(guest=guest)
        if operation == "create":
            create_data = {"channel_id": channel_id}
            if target == "self":
                if guest:
                    create_data["guest_id"] = guest.id
                else:
                    create_data["partner_id"] = partner.id
            else:
                create_data["partner_id"] = self.other_user_2.partner_id.id
            ChannelMemberAsUser.create(create_data)
        else:
            domain = [("channel_id", "=", channel_id)]
            if target == "self":
                if guest:
                    domain.append(("guest_id", "=", guest.id))
                else:
                    domain.append(("partner_id", "=", partner.id))
            else:
                domain.append(("partner_id", "=", self.other_user.partner_id.id))
            member = ChannelMemberAsUser.sudo().search(domain).sudo(False)
            self.assertEqual(len(member), 1, "should find the target member")
            if operation == "read":
                self.assertEqual(len(ChannelMemberAsUser.search(domain)), 1 if result else 0)
                member.read(["custom_channel_name"])
            elif operation == "write":
                member.write({"custom_channel_name": "new name"})
            elif operation == "unlink":
                member.unlink()