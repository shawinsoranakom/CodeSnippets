def _check_before_creating_new_session(self):
        self.ensure_one()
        # Check validity of programs before opening a new session
        invalid_reward_products_msg = ''
        for reward in self._get_program_ids().reward_ids:
            if reward.reward_type == 'product':
                for product in reward.reward_product_ids:
                    if product.available_in_pos:
                        continue
                    invalid_reward_products_msg += "\n\t"
                    invalid_reward_products_msg += _(
                        "Program: %(name)s, Reward Product: `%(reward_product)s`",
                        name=reward.program_id.name,
                        reward_product=product.name,
                    )
        gift_card_programs = self._get_program_ids().filtered(lambda p: p.program_type == 'gift_card')
        for product in gift_card_programs.mapped('rule_ids.valid_product_ids'):
            if product.available_in_pos:
                continue
            invalid_reward_products_msg += "\n\t"
            invalid_reward_products_msg += _(
                "Program: %(name)s, Rule Product: `%(rule_product)s`",
                name=reward.program_id.name,
                rule_product=product.name,
            )

        if invalid_reward_products_msg:
            prefix_error_msg = _("To continue, make the following reward products available in Point of Sale.")
            raise UserError(f"{prefix_error_msg}\n{invalid_reward_products_msg}")  # pylint: disable=missing-gettext
        if gift_card_programs:
            for gc_program in gift_card_programs:
                # Do not allow a gift card program with more than one rule or reward, and check that they make sense
                if len(gc_program.reward_ids) > 1:
                    raise UserError(_('Invalid gift card program. More than one reward.'))
                elif len(gc_program.rule_ids) > 1:
                    raise UserError(_('Invalid gift card program. More than one rule.'))
                rule = gc_program.rule_ids
                if rule.reward_point_amount != 1 or rule.reward_point_mode != 'money':
                    raise UserError(_('Invalid gift card program rule. Use 1 point per currency spent.'))
                reward = gc_program.reward_ids
                if reward.reward_type != 'discount' or reward.discount_mode != 'per_point' or reward.discount != 1:
                    raise UserError(_('Invalid gift card program reward. Use 1 currency per point discount.'))
                if not gc_program.mail_template_id:
                    raise UserError(_('There is no email template on the gift card program and your pos is set to print them.'))
                if not gc_program.pos_report_print_id:
                    raise UserError(_('There is no print report on the gift card program and your pos is set to print them.'))

        return super()._check_before_creating_new_session()