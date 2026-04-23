def write(self, vals):
        cost_in_vals = 'points_cost' in vals
        if cost_in_vals:
            previous_vals = {line: (line.points_cost, line.coupon_id) for line in self}
        res = super().write(vals)
        if cost_in_vals:
            # Update our coupon points if the order is in a confirmed state
            for line, (previous_cost, previous_coupon) in previous_vals.items():
                if line.state != 'sale':
                    continue
                if line.points_cost != previous_cost or line.coupon_id != previous_coupon:
                    previous_coupon.points += previous_cost
                    line.coupon_id.points -= line.points_cost
        return res