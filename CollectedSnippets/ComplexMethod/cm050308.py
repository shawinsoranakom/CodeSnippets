def _recompute_rank(self):
        """
        The caller should filter the users on karma > 0 before calling this method
        to avoid looping on every single users

        Compute rank of each user by user.
        For each user, check the rank of this user
        """

        ranks = [{'rank': rank, 'karma_min': rank.karma_min} for rank in
                 self.env['gamification.karma.rank'].search([], order="karma_min DESC")]

        # 3 is the number of search/requests used by rank in _recompute_rank_bulk()
        if len(self) > len(ranks) * 3:
            self._recompute_rank_bulk()
            return

        for user in self:
            old_rank = user.rank_id
            if user.karma == 0 and ranks:
                user.write({'next_rank_id': ranks[-1]['rank'].id})
            else:
                for i in range(0, len(ranks)):
                    if user.karma >= ranks[i]['karma_min']:
                        user.write({
                            'rank_id': ranks[i]['rank'].id,
                            'next_rank_id': ranks[i - 1]['rank'].id if 0 < i else False
                        })
                        break
            if old_rank != user.rank_id:
                user._rank_changed()