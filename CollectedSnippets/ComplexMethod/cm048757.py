def _get_child_lines(self):
        """
        Return a tax-wise summary of account move lines linked to section.
        Groups lines by their tax IDs and computes subtotal and total for each group.
        """
        self.ensure_one()
        children_lines = self.move_id.invoice_line_ids.filtered(lambda l: self in {l.parent_id, l.parent_id.parent_id})
        subsection_lines = children_lines.filtered(lambda l: l.display_type == 'line_subsection')
        direct_children_lines = children_lines.filtered(lambda l: l.parent_id == self and l.display_type != 'line_subsection')
        section_subtotal = sum(l.price_subtotal for l in children_lines)
        section_total = sum(l.price_total for l in children_lines)
        result = [{
            'name': self.name,
            'taxes': [tax.tax_label for tax in children_lines.tax_ids if tax.tax_label],
            'price_subtotal': section_subtotal,
            'price_total': section_total,
            'display_type': self.display_type,
            'quantity': 0,
            'line_uom': False,
            'product_uom': False,
            'discount': 0.0,
        }]

        if not self.collapse_composition:
            for line in direct_children_lines:
                result.append({
                    'name': line.name,
                    'taxes': [tax.tax_label for tax in line.tax_ids if tax.tax_label] if not self.collapse_prices else [],
                    'price_subtotal': line.price_subtotal,
                    'price_total': line.price_total,
                    'display_type': line.display_type,
                    'quantity': line.quantity,
                    'line_uom': line.product_uom_id,
                    'product_uom': line.product_id.uom_id,
                    'discount': line.discount,
                })

        for subsection_line in subsection_lines:
            lines_in_subsection = children_lines.filtered(lambda l: l.parent_id == subsection_line)
            for taxes, lines_for_tax_group in groupby(lines_in_subsection, key=lambda l: l.tax_ids):
                lines_for_tax_group = sum(lines_for_tax_group, start=self.env['account.move.line'])
                tax_labels = [tax.tax_label for tax in taxes if tax.tax_label]
                subtotal = sum(l.price_subtotal for l in lines_for_tax_group)
                total = sum(l.price_total for l in lines_for_tax_group)
                if not subtotal and not tax_labels:
                    continue
                if subsection_line.collapse_composition or self.collapse_composition:
                    result.append({
                        'name': subsection_line.name,
                        'taxes': tax_labels,
                        'price_subtotal': subtotal,
                        'price_total': total,
                        'display_type': 'product',
                        'quantity': 1,
                        'line_uom': False,
                        'product_uom': False,
                        'discount': 0.0,
                    })
                else:
                    for line in subsection_line | lines_for_tax_group:
                        result.append({
                            'name': line.name,
                            'taxes': tax_labels if line == subsection_line else [],
                            'price_subtotal': subtotal if line == subsection_line else line.price_subtotal,
                            'price_total': total if line == subsection_line else line.price_total,
                            'display_type': line.display_type,
                            'quantity': line.quantity,
                            'line_uom': line.product_uom_id,
                            'product_uom': line.product_id.uom_id,
                            'discount': line.discount,
                        })
        return result or [{
            'name': self.name,
            'taxes': [],
            'price_subtotal': 0.0,
            'price_total': 0.0,
            'quantity': 0,
            'display_type': 'product',
        }]