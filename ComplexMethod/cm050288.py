def _auto_apply_rewards(self):
        """
        Tries to auto apply claimable rewards.

        It must answer to the following rules:
         - Must not be from a nominative program
         - The reward must be the only reward of the program
         - The reward may not be a multi product reward

        Returns True if any reward was claimed else False
        """
        self.ensure_one()

        claimed_reward_count = 0
        claimable_rewards = self._get_claimable_rewards()
        for coupon, rewards in claimable_rewards.items():
            if (
                len(coupon.program_id.reward_ids) != 1
                or coupon.program_id.is_nominative
                or (rewards.reward_type == 'product' and rewards.multi_product)
                or rewards in self.disabled_auto_rewards
                or rewards in self.order_line.reward_id
            ):
                continue

            try:
                res = self._apply_program_reward(rewards, coupon)
                if 'error' not in res:
                    claimed_reward_count += 1
            except UserError:
                pass

        return bool(claimed_reward_count)