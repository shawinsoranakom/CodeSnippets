def unlink(self):
        # Remove related reward lines
        reward_coupon_set = {(l.reward_id, l.coupon_id, l.reward_identifier_code) for l in self if l.reward_id}
        related_lines = self.env['sale.order.line']
        related_lines |= self.order_id.order_line.filtered(lambda l: (l.reward_id, l.coupon_id, l.reward_identifier_code) in reward_coupon_set)
        # Remove the line's coupon from order if it is the last line using that coupon
        coupons_to_unlink = self.env['loyalty.card']
        for line in self:
            if line.coupon_id:
                # 2 cases:
                #  case 1: coupon has been applied directly
                #  case 2: coupon was created from a program
                if line.coupon_id in line.order_id.applied_coupon_ids:
                    line.order_id.applied_coupon_ids -= line.coupon_id
                elif line.coupon_id.order_id == line.order_id and line.coupon_id.program_id.applies_on == 'current' and\
                    not any(oLine.coupon_id == line.coupon_id and oLine not in related_lines for oLine in line.order_id.order_line):
                    # ondelete='restrict' would prevent deletion of the coupon unlink after unlinking lines
                    coupons_to_unlink |= line.coupon_id
                    line.order_id.code_enabled_rule_ids = line.order_id.code_enabled_rule_ids.filtered(lambda r: r.program_id != line.coupon_id.program_id)
        # Give back the points if the order is confirmed, points are given back if the order is cancelled but in this case we need to do it directly
        for line in related_lines:
            if line.state == 'sale':
                line.coupon_id.points += line.points_cost
        res = super(SaleOrderLine, self | related_lines).unlink()
        coupons_to_unlink.sudo().unlink()
        return res