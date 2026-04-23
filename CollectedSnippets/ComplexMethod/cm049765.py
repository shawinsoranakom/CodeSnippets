def test_discuss_mention_suggestions_priority(self):
        name = uuid4()  # unique name to avoid conflict with already existing users
        self.env['res.partner'].create([{'name': f'{name}-{i}-not-user'} for i in range(0, 2)])
        for i in range(0, 2):
            mail_new_test_user(self.env, login=f'{name}-{i}-portal-user', groups='base.group_portal')
            mail_new_test_user(self.env, login=f'{name}-{i}-internal-user', groups='base.group_user')

        # suggest portal user of this company in another company
        suggested_partners = self.env["res.partner"].with_user(self.user_employee_c2).get_mention_suggestions("portal-user")

        porter_user_suggested = [
            p for p in suggested_partners['res.partner']
            if p["name"] == f'{name}-1-portal-user (base.group_portal)'
        ]
        self.assertEqual(len(porter_user_suggested), 1, "porter_user_suggested should contain one user")
        store_data = self.env["res.partner"].get_mention_suggestions(name, limit=5)
        partners_format = store_data["res.partner"]
        self.assertEqual(len(partners_format), 5, "should have found limit (5) partners")
        # return format for user is either a dict (there is a user and the dict is data) or a list of command (clear)
        self.assertEqual(
            [
                next(
                    (
                        not u["share"]
                        for u in store_data["res.users"]
                        if u["id"] == p["main_user_id"]
                    ),
                    False,
                )
                for p in partners_format
            ],
            [True, True, False, False, False],
            "should return internal users in priority",
        )
        self.assertEqual(
            [bool(p["main_user_id"]) for p in partners_format],
            [True, True, True, True, False],
            "should return partners without users last",
        )