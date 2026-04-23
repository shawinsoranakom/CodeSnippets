def _update_programs_and_rewards(self):
        """
        Updates applied programs's given points with the current state of the order.
        Checks automatic programs for applicability.
        Updates applied rewards using the new points and the current state of the order (for example with % discounts).
        """
        self.ensure_one()

        # +===================================================+
        # |       STEP 1: Retrieve all applicable programs    |
        # +===================================================+

        # Automatically load in eWallet and loyalty cards coupons with previously received points
        if self._allow_nominative_programs():
            loyalty_card = self.env['loyalty.card'].search([
                ('id', 'not in', self.applied_coupon_ids.ids),
                ('partner_id', '=', self.partner_id.id),
                ('points', '>', 0),
                '|', ('program_id.program_type', '=', 'ewallet'),
                     '&', ('program_id.program_type', '=', 'loyalty'),
                          ('program_id.applies_on', '!=', 'current'),
            ])
            if loyalty_card:
                self.applied_coupon_ids += loyalty_card
        # Programs that are applied to the order and count points
        points_programs = self._get_points_programs()
        # Coupon programs that require the program's rules to match but do not count for points
        coupon_programs = self.applied_coupon_ids.program_id
        # Programs that are automatic and not yet applied
        program_domain = self._get_program_domain()
        domain = Domain.AND([program_domain, [('id', 'not in', points_programs.ids), ('trigger', '=', 'auto'), ('rule_ids.mode', '=', 'auto')]])
        automatic_programs = self.env['loyalty.program'].search(domain).filtered(lambda p:
            not p.limit_usage or p.total_order_count < p.max_usage)

        all_programs_to_check = points_programs | coupon_programs | automatic_programs
        all_coupons = self.coupon_point_ids.coupon_id | self.applied_coupon_ids
        # First basic check using the program_domain -> for example if a program gets archived mid quotation
        domain_matching_programs = all_programs_to_check.filtered_domain(program_domain)
        all_programs_status = {p: {'error': 'error'} for p in all_programs_to_check - domain_matching_programs}
        # Compute applicability and points given for all programs that passed the domain check
        # Note that points are computed with reward lines present
        all_programs_status.update(self._program_check_compute_points(domain_matching_programs))
        # Delay any unlink to the end of the function since they cause a full cache invalidation
        lines_to_unlink = self.env['sale.order.line']
        coupons_to_unlink = self.env['loyalty.card']
        point_entries_to_unlink = self.env['sale.order.coupon.points']
        # Remove any coupons that are expired
        if initial_coupons := self.applied_coupon_ids:
            check_date = self._get_confirmed_tx_create_date()
            self.applied_coupon_ids = initial_coupons.filtered(
                lambda c: not c.expiration_date or c.expiration_date >= check_date,
            )
            removed = initial_coupons - self.applied_coupon_ids
            lines_to_unlink |= self.order_line.filtered(lambda sol: sol.coupon_id in removed)
        point_ids_per_program = defaultdict(lambda: self.env['sale.order.coupon.points'])
        for pe in self.coupon_point_ids:
            # Update coupons that were created for Public User
            if pe.coupon_id.partner_id.is_public and not self.partner_id.is_public:
                pe.coupon_id.partner_id = self.partner_id
            # Remove any point entry for a coupon that does not belong to the customer
            if pe.coupon_id.partner_id and pe.coupon_id.partner_id != self.partner_id:
                pe.points = 0
                point_entries_to_unlink |= pe
            else:
                point_ids_per_program[pe.coupon_id.program_id] |= pe

        # +==========================================+
        # |       STEP 2: Update applied programs    |
        # +==========================================+

        # Programs that were not applied via a coupon
        for program in points_programs:
            status = all_programs_status[program]
            program_point_entries = point_ids_per_program[program]
            if 'error' in status:
                # Program is not applicable anymore
                coupons_from_order = program_point_entries.coupon_id.filtered(lambda c: c.order_id == self)
                all_coupons -= coupons_from_order
                # Invalidate those lines so that they don't impact anything further down the line
                program_reward_lines = self.order_line.filtered(lambda l: l.coupon_id in coupons_from_order)
                program_reward_lines._reset_loyalty(True)
                lines_to_unlink |= program_reward_lines
                # Delete coupon created by this order for this program if it is not nominative
                if not program.is_nominative:
                    coupons_to_unlink |= coupons_from_order
                else:
                    # Only remove the coupon_point_id
                    point_entries_to_unlink |= program_point_entries
                    point_entries_to_unlink.points = 0
                # Remove the code activated rules
                self.code_enabled_rule_ids -= program.rule_ids
            else:
                # Program stays applicable, update our points
                all_point_changes = [p for p in status['points'] if p]
                if not all_point_changes and program.is_nominative:
                    all_point_changes = [0]
                for pe, points in zip(program_point_entries.sudo(), all_point_changes):
                    pe.points = points
                if len(program_point_entries) < len(all_point_changes):
                    new_coupon_points = all_point_changes[len(program_point_entries):]
                    # next_order_coupons should be linked to the order's partner
                    partner_id = program.program_type == 'next_order_coupons' and self.partner_id.id
                    # NOTE: Maybe we could batch the creation of coupons across multiple programs but this really only applies to gift cards
                    new_coupons = self.env['loyalty.card'].with_context(loyalty_no_mail=True, tracking_disable=True).create([{
                        'program_id': program.id,
                        'partner_id': partner_id,
                        'points': 0,
                        'order_id': self.id,
                    } for _ in new_coupon_points])
                    self._add_points_for_coupon({coupon: x for coupon, x in zip(new_coupons, new_coupon_points)})
                elif len(program_point_entries) > len(all_point_changes):
                    point_ids_to_unlink = program_point_entries[len(all_point_changes):]
                    all_coupons -= point_ids_to_unlink.coupon_id
                    coupons_to_unlink |= point_ids_to_unlink.coupon_id
                    point_ids_to_unlink.points = 0

        # Programs applied using a coupon
        applied_coupon_per_program = defaultdict(lambda: self.env['loyalty.card'])
        for coupon in self.applied_coupon_ids:
            applied_coupon_per_program[coupon.program_id] |= coupon
        for program in coupon_programs:
            if program not in domain_matching_programs or\
                (program.applies_on == 'current' and 'error' in all_programs_status[program]):
                program_reward_lines = self.order_line.filtered(lambda l: l.coupon_id in applied_coupon_per_program[program])
                program_reward_lines._reset_loyalty(True)
                lines_to_unlink |= program_reward_lines
                self.applied_coupon_ids -= applied_coupon_per_program[program]
                all_coupons -= applied_coupon_per_program[program]

        # +==========================================+
        # |       STEP 3: Update reward lines        |
        # +==========================================+

        # We will reuse these lines as much as possible, this resets the order in a reward-less state
        reward_line_pool = self.order_line.filtered(lambda l: l.reward_id and l.coupon_id)._reset_loyalty()
        seen_rewards = set()
        line_rewards = []
        payment_rewards = [] # gift_card and ewallet are considered as payments and should always be applied last
        for line in self.order_line:
            if line.reward_identifier_code in seen_rewards or not line.reward_id or\
                not line.coupon_id:
                continue
            seen_rewards.add(line.reward_identifier_code)
            if line.reward_id.program_id.is_payment_program:
                payment_rewards.append((line.reward_id, line.coupon_id, line.reward_identifier_code, line.product_id))
            else:
                line_rewards.append((line.reward_id, line.coupon_id, line.reward_identifier_code, line.product_id))

        for reward_key in itertools.chain(line_rewards, payment_rewards):
            coupon = reward_key[1]
            reward = reward_key[0]
            program = reward.program_id
            points = self._get_real_points_for_coupon(coupon)
            if coupon not in all_coupons or points < reward.required_points or program not in domain_matching_programs:
                # Reward is not applicable anymore, the reward lines will simply be removed at the end of this function
                continue
            try:
                values_list = self._get_reward_line_values(reward, coupon, product=reward_key[3])
            except UserError:
                # It could happen that we have nothing to discount after changing the order.
                values_list = []
            reward_line_pool = self._write_vals_from_reward_vals(values_list, reward_line_pool, delete=False)

        lines_to_unlink |= reward_line_pool

        # +==========================================+
        # |       STEP 4: Apply new programs         |
        # +==========================================+

        for program in automatic_programs:
            program_status = all_programs_status[program]
            if 'error' in program_status:
                continue
            self.__try_apply_program(program, False, program_status)

        # +==========================================+
        # |       STEP 5: Cleanup                    |
        # +==========================================+

        order_line_update = [(Command.DELETE, line.id) for line in lines_to_unlink]
        if order_line_update:
            self.write({'order_line': order_line_update})
        if coupons_to_unlink:
            coupons_to_unlink.sudo().unlink()
        if point_entries_to_unlink:
            point_entries_to_unlink.sudo().unlink()