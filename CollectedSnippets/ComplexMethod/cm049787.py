def test_02_sub_channel_members_sync_with_parent(self):
        parent = self.env["discuss.channel"].create({"name": "General"})
        parent.action_unfollow()
        self.assertFalse(any(m.is_self for m in parent.channel_member_ids))
        parent._create_sub_channel()
        sub_channel = parent.sub_channel_ids[0]
        # Member created for sub channel (_create_sub_channel): should also be
        # created for the parent channel.
        self.assertTrue(any(m.is_self for m in parent.channel_member_ids))
        self.assertTrue(any(m.is_self for m in sub_channel.channel_member_ids))
        # Member removed from parent channel: should also be removed from the sub
        # channel.
        parent.action_unfollow()
        self.assertFalse(any(m.is_self for m in parent.channel_member_ids))
        self.assertFalse(any(m.is_self for m in sub_channel.channel_member_ids))
        # Member created for sub channel (add_members): should also be created
        # for parent.
        sub_channel._add_members(users=self.env.user)
        self.assertTrue(any(m.is_self for m in parent.channel_member_ids))
        self.assertTrue(any(m.is_self for m in sub_channel.channel_member_ids))