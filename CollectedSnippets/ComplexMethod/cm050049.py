def _compute_parent_id(self):
        option_lines = set(self)
        for template, lines in self.grouped('sale_order_template_id').items():
            if not template:
                lines.parent_id = False
                continue
            last_section = False
            last_sub = False
            for line in template.sale_order_template_line_ids.sorted('sequence'):
                if line.display_type == 'line_section':
                    last_section = line
                    if line in option_lines:
                        line.parent_id = False
                    last_sub = False
                elif line.display_type == 'line_subsection':
                    if line in option_lines:
                        line.parent_id = last_section
                    last_sub = line
                elif line in option_lines:
                    line.parent_id = last_sub or last_section