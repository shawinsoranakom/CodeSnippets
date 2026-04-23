def _execute_subtests(self, message, subtests):
        for data_user, allowed, *args in subtests:
            route_kw = args[0] if args else {}
            kwargs = args[1] if len(args) > 1 else {}
            user, guest = self._authenticate_pseudo_user(data_user)
            with self.subTest(user=user.name, guest=guest.name, route_kw=route_kw):
                if allowed:
                    self._add_reaction(message, self.reaction, route_kw)
                    reactions = message.reaction_ids
                    self.assertEqual(len(reactions), 1)
                    expected_partner = kwargs.get("partner")
                    if guest and not expected_partner:
                        self.assertEqual(reactions.guest_id, guest)
                    else:
                        self.assertEqual(reactions.partner_id, expected_partner or user.partner_id)
                    self._remove_reaction(message, self.reaction, route_kw)
                    self.assertFalse(message.reaction_ids)
                else:
                    with self.assertRaises(
                        JsonRpcException, msg="add reaction should raise NotFound"
                    ):
                        self._add_reaction(message, self.reaction, route_kw)
                    with self.assertRaises(
                        JsonRpcException, msg="remove reaction should raise NotFound"
                    ):
                        self._remove_reaction(message, self.reaction, route_kw)