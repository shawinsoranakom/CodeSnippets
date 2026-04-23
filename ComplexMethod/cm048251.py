def _try_apply_program(self, program, coupon=None):
        """
        Tries to apply a program using the coupon if provided.

        This function provides the full routine to apply a program, it will check for applicability
        aswell as creating the necessary coupons and co-models to give the points to the customer.

        This function does not apply any reward to the order, rewards have to be given manually.

        Returns a dict containing the error message or containing the associated coupon(s).
        """
        self.ensure_one()
        # Basic checks
        if not program.filtered_domain(self._get_program_domain()):
            return {'error': _("The program is not available for this order.")}
        elif program in self._get_applied_programs():
            return {'error': _("This program is already applied to this order."), 'already_applied': True}
        elif program.reward_ids:
            global_rewards = program.reward_ids.filtered('is_global_discount')
            applied_global_reward = self._get_applied_global_discount()
            best_global_rewards = max(
                global_rewards,
                key=lambda reward: self._get_discount_amount(
                    reward, self._discountable_amount(applied_global_reward)
                )
            ) if len(global_rewards) > 1 else global_rewards
            if (
                best_global_rewards
                and applied_global_reward
                and self._best_global_discount_already_applied(applied_global_reward, best_global_rewards)
            ):
                return {'error': _(
                    "This discount (%(discount)s) is not compatible with \"%(other_discount)s\". "
                    "Please remove it in order to apply this one.",
                    discount=best_global_rewards.description,
                    other_discount=applied_global_reward.description
                )}
        # Check for applicability from the program's triggers/rules.
        # This step should also compute the amount of points to give for that program on that order.
        status = self._program_check_compute_points(program)[program]
        if 'error' in status:
            return status
        return self.__try_apply_program(program, coupon, status)