def _try_apply_code(self, code):
        """
        Tries to apply a promotional code to the sales order.
        It can be either from a coupon or a program rule.

        Returns a dict with the following possible keys:
         - 'not_found': Populated with True if the code did not yield any result.
         - 'error': Any error message that could occur.
         OR The result of `_get_claimable_rewards` with the found or newly created coupon, it will be empty if the coupon was consumed completely.
        """
        self.ensure_one()

        base_domain = self._get_trigger_domain()
        domain = Domain.AND([base_domain, [('mode', '=', 'with_code'), ('code', '=', code)]])
        rule = self.env['loyalty.rule'].search(domain)
        program = rule.program_id
        coupon = False
        check_date = self._get_confirmed_tx_create_date()

        if rule in self.code_enabled_rule_ids:
            return {'error': _("This promo code is already applied.")}

        # No trigger was found from the code, try to find a coupon
        if not program:
            coupon = self.env['loyalty.card'].search([('code', '=', code)])
            if not coupon or\
                not coupon.program_id.active or\
                not coupon.program_id.reward_ids or\
                not coupon.program_id.filtered_domain(self._get_program_domain()):
                return {'error': _("This code is invalid (%s).", code), 'not_found': True}
            if coupon.expiration_date and coupon.expiration_date < check_date:
                return {'error': _("This coupon is expired.")}
            elif coupon.points < min(coupon.program_id.reward_ids.mapped('required_points')):
                return {'error': _("This coupon has already been used.")}
            program = coupon.program_id

        if not program or not program.active:
            return {'error': _("This code is invalid (%s).", code), 'not_found': True}
        elif program.program_type in ('loyalty', 'ewallet'):
            return {'error': _("This program cannot be applied with code.")}

        # Lock the loyalty program row to block several processes that try to
        # read it at the same time. We also use NOWAIT to make sure we trigger a
        # serialization error when the processes don't have the lock and thus,
        # trigger a retry of the transaction.
        self.env.cr.execute("""
            SELECT id FROM loyalty_program WHERE id=%s FOR UPDATE NOWAIT
        """, (program.id,))

        if (program.limit_usage and program.total_order_count >= program.max_usage):
            return {'error': _("This code is expired (%s).", code)}

        # Rule will count the next time the points are updated
        if rule:
            self.code_enabled_rule_ids |= rule
        program_is_applied = program in self._get_points_programs()
        # Condition that need to apply program (if not applied yet):
        # current -> always
        # future -> if no coupon
        # nominative -> non blocking if card exists with points
        if coupon:
            self.applied_coupon_ids += coupon
        if program_is_applied:
            # Update the points for our programs, this will take the new trigger in account
            self._update_programs_and_rewards()
        elif program.applies_on != 'future' or not coupon:
            apply_result = self._try_apply_program(program, coupon)
            if 'error' in apply_result and (not program.is_nominative or (program.is_nominative and not coupon)):
                if rule:
                    self.code_enabled_rule_ids -= rule
                if coupon and not apply_result.get('already_applied', False):
                    self.applied_coupon_ids -= coupon
                return apply_result
            coupon = apply_result.get('coupon', self.env['loyalty.card'])
        return self._get_claimable_rewards(forced_coupons=coupon)