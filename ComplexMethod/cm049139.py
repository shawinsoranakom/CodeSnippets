def _compute_parent_id(self):
        purchase_order_lines = set(self)
        for order, lines in self.grouped('order_id').items():
            if not order:
                lines.parent_id = False
                continue
            last_section = False
            last_sub = False
            for line in order.order_line.sorted('sequence'):
                if line.display_type == 'line_section':
                    last_section = line
                    if line in purchase_order_lines:
                        line.parent_id = False
                    last_sub = False
                elif line.display_type == 'line_subsection':
                    if line in purchase_order_lines:
                        line.parent_id = last_section
                    last_sub = line
                elif line in purchase_order_lines:
                    line.parent_id = last_sub or last_section