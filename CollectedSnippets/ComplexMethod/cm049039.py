def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        section_line_ids = []
        subsection_line_ids = []
        precision = self.env['decimal.precision'].precision_get('Product Unit')

        for line in self.order_line:
            if line.display_type == 'line_section':
                section_line_ids = [line.id]  # Start a new section.
                subsection_line_ids = []
                continue
            if line.display_type == 'line_subsection':
                subsection_line_ids = [line.id]  # Start a new subsection.
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                # If the invoicable line is under subsection
                if subsection_line_ids:
                    if line.display_type:
                        subsection_line_ids.append(line.id)
                        continue
                    # Extend the subsection lines too if altleast one invoicable line is under subsection
                    invoiceable_line_ids.extend(section_line_ids + subsection_line_ids)
                    subsection_line_ids = []
                    section_line_ids = []
                # If the invoicable line is under section
                elif section_line_ids:
                    if line.display_type:
                        section_line_ids.append(line.id)
                        continue
                    invoiceable_line_ids.extend(section_line_ids)
                    section_line_ids = []
                    subsection_line_ids = []
                invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)