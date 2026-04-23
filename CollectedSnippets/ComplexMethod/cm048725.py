def _compute_name(self):
        def get_name(line):
            values = []
            if line.move_id.partner_id.lang:
                product = line.product_id.with_context(lang=line.move_id.partner_id.lang)
            elif line.partner_id.lang:
                product = line.product_id.with_context(lang=line.partner_id.lang)
            else:
                product = line.product_id
            if not product:
                return False

            if line.journal_id.type == 'sale':
                values.append(product.display_name)
                if product.description_sale:
                    values.append(product.description_sale)
            elif line.journal_id.type == 'purchase':
                values.append(product.display_name)
                if product.description_purchase:
                    values.append(product.description_purchase)
            return '\n'.join(values) if values else False

        term_by_move = (self.move_id.line_ids | self).filtered(lambda l: l.display_type == 'payment_term').sorted(lambda l: l.date_maturity or date.max).grouped('move_id')
        for line in self.filtered(lambda l: l.move_id.inalterable_hash is False):
            if line.display_type == 'payment_term':
                term_lines = term_by_move.get(line.move_id, self.env['account.move.line'])
                n_terms = len(line.move_id.invoice_payment_term_id.line_ids)
                if line.move_id.payment_reference and line.move_id.ref and line.move_id.payment_reference != line.move_id.ref:
                    name = f'{line.move_id.ref} - {line.move_id.payment_reference}'
                elif line.move_id.payment_reference:
                    name = line.move_id.payment_reference
                elif line.move_id.move_type in ['in_invoice', 'in_refund'] and line.move_id.ref:
                    name = line.move_id.ref
                else:
                    name = False

                if n_terms > 1:
                    index = term_lines._ids.index(line.id) if line in term_lines else len(term_lines)

                    name = _('%(name)s installment #%(number)s', name=name if name else '', number=index + 1).lstrip()
                if name:
                    line.name = name
            if not line.product_id or line.display_type in ('line_section', 'line_subsection', 'line_note'):
                continue

            if not line.name or line._origin.name == get_name(line._origin) or line.product_id != line._origin.product_id:
                line.name = get_name(line)