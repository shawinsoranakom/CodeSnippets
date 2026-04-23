def reflect_cancelled_sol(self, isCancelled):
        if self.env.user.has_group('point_of_sale.group_pos_user'):
            for invoice in self:
                for pos_order_line in invoice.pos_order_ids.mapped('lines'):
                    if pos_order_line.sale_order_line_id:
                        if isCancelled and "(Cancelled)" not in pos_order_line.sale_order_line_id.name:
                            name = _("%(old_name)s (Cancelled)", old_name=pos_order_line.sale_order_line_id.name)
                            pos_order_line.sale_order_line_id.name = name
                        elif not isCancelled and "(Cancelled)" in pos_order_line.sale_order_line_id.name:
                            pos_order_line.sale_order_line_id.name = pos_order_line.sale_order_line_id.name.replace(" (Cancelled)", "")