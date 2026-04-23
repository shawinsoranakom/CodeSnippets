def test_member_based_channel_naming(self):
        john = mail_new_test_user(self.env, groups="base.group_user", login="john")
        bob = mail_new_test_user(self.env, groups="base.group_user", login="bob")
        alice = mail_new_test_user(self.env, groups="base.group_user", login="alice")
        eve = mail_new_test_user(self.env, groups="base.group_user", login="eve")
        group = self.env["discuss.channel"].create({"name": "", "channel_type": "group"})
        channel = self.env["discuss.channel"].create({"name": "General"})

        # Each test case represents a flow of member changes on a given channel.
        # The format is: (channel, flow) where `flow` is a list of tuples
        # (user, operation, expected_users).
        #
        # Those cases ensure that we only send `channel_name_member_ids` updates
        # for channels listed in `_member_based_naming_channel_types`, and only
        # when relevant members (those contributing to the computed name) are affected.
        cases = [
            # Channel does not use member-based naming (not in `_member_based_naming_channel_types`).
            (
                channel,
                [(john, "add", False), (john, "remove", False)],
            ),
            # Group uses member-based naming (in `_member_based_naming_channel_types`).
            # Name is computed from the first 3 members. Updates are only sent when those change.
            (
                group,
                [
                    (john, "add", [self.env.user, john]),
                    (bob, "add", [self.env.user, john, bob]),
                    # Alice is added: we already have 3 members to compute the name, no update.
                    (alice, "add", False),
                    (eve, "add", False),
                    # Eve is removed: not taken into account for name computation, no update.
                    (eve, "remove", False),
                    # John is removed: was used in naming, update.
                    (john, "remove", [self.env.user, bob, alice]),
                ],
            ),
        ]

        for channel, flow in cases:
            with self.subTest(
                f"Test member-based channel name: channel_type={channel.channel_type}, channel_name={channel.name}"
            ):
                for user, operation, expected_users in flow:
                    self._reset_bus()
                    if operation == "add":
                        channel._add_members(users=user, post_joined_message=False)
                    else:
                        channel.with_user(user).action_unfollow()
                    self.cr.precommit.run()
                    matching_data = None
                    for notification in self.env["bus.bus"].search(
                        [("channel", "=", json_dump((self.cr.dbname, "discuss.channel", channel.id)))]
                    ):
                        message = json.loads(notification.message)
                        if message["type"] != "mail.record/insert":
                            continue
                        if "discuss.channel" not in message["payload"]:
                            continue
                        matching_data = next(
                            (
                                data
                                for data in message["payload"]["discuss.channel"]
                                if data["id"] == channel.id and "channel_name_member_ids" in data
                            ),
                            None,
                        )
                        if matching_data:
                            break

                    if expected_users is False:
                        self.assertIsNone(
                            matching_data, "Unexpected channel_name_member_ids update"
                        )
                    else:
                        self.assertIsNotNone(
                            matching_data, "Missing channel_name_member_ids update"
                        )
                        expected_member_ids = [
                            member.id
                            for member in channel.channel_member_ids
                            if member.partner_id.main_user_id in expected_users
                        ]
                        self.assertEqual(
                            matching_data["channel_name_member_ids"], expected_member_ids
                        )