def test_01_switch_rank(self):

        self.assertEqual(len(self.users), 35)

        self.rank_3.karma_min = 100
        # rank_1 -> rank_3 -> rank_2 -> rank_4

        self.assertEqual(
            len(self.rank_1.user_ids & self.users),
            len([u for u in self.users if u.karma >= self.rank_1.karma_min and u.karma < self.rank_3.karma_min])
        )
        self.assertEqual(
            len(self.rank_3.user_ids & self.users),
            len([u for u in self.users if u.karma >= self.rank_3.karma_min and u.karma < self.rank_2.karma_min])
        )
        self.assertEqual(
            len(self.rank_2.user_ids & self.users),
            len([u for u in self.users if u.karma >= self.rank_2.karma_min and u.karma < self.rank_4.karma_min])
        )
        self.assertEqual(
            len(self.rank_4.user_ids & self.users),
            len([u for u in self.users if u.karma >= self.rank_4.karma_min])
        )