def _sync_non_deductible_base_lines(self, container):
        def has_non_deductible_lines(move):
            return (
                move.state == 'draft'
                and move.is_purchase_document()
                and any(move.line_ids.filtered(lambda line: line.display_type == 'product' and line.deductible_amount < 100))
            )

        # Collect data to avoid recomputing value unecessarily
        product_lines_before = {
            move: Counter(
                (line.name, line.price_subtotal, line.tax_ids, line.deductible_amount, line.account_id)
                for line in move.line_ids
                if line.display_type == 'product'
            )
            for move in container['records']
        }

        yield

        to_delete = []
        to_create = []
        for move in container['records']:
            product_lines_now = Counter(
                (line.name, line.price_subtotal, line.tax_ids, line.deductible_amount, line.account_id)
                for line in move.line_ids
                if line.display_type == 'product'
            )

            has_changed_product_lines = bool(
                product_lines_before.get(move, Counter()) - product_lines_now
                or product_lines_now - product_lines_before.get(move, Counter())
            )
            if not has_changed_product_lines:
                # No difference between before and now, then nothing to do
                continue

            non_deductible_base_lines = move.line_ids.filtered(lambda line: line.display_type in ('non_deductible_product', 'non_deductible_product_total'))
            to_delete += non_deductible_base_lines.ids

            if not has_non_deductible_lines(move):
                continue

            non_deductible_base_total = 0.0
            non_deductible_base_currency_total = 0.0

            sign = move.direction_sign
            rate = move.invoice_currency_rate

            for line in move.line_ids.filtered(lambda line: line.display_type == 'product'):
                if float_compare(line.deductible_amount, 100, precision_rounding=2) == 0:
                    continue

                percentage = (1 - line.deductible_amount / 100)
                non_deductible_subtotal = line.currency_id.round(line.price_subtotal * percentage)
                non_deductible_base = line.currency_id.round(sign * non_deductible_subtotal)
                non_deductible_base_currency = line.company_currency_id.round(sign * non_deductible_subtotal / rate) if rate else 0.0
                non_deductible_base_total += non_deductible_base
                non_deductible_base_currency_total += non_deductible_base_currency

                to_create.append({
                    'move_id': move.id,
                    'account_id': line.account_id.id,
                    'display_type': 'non_deductible_product',
                    'name': line.name,
                    'balance': -1 * non_deductible_base,
                    'amount_currency': -1 * non_deductible_base_currency,
                    'tax_ids': [Command.set(line.tax_ids.filtered(lambda tax: tax.amount_type != 'fixed').ids)],
                    'sequence': line.sequence + 1,
                })

            to_create.append({
                'move_id': move.id,
                'account_id': (
                    move.journal_id.non_deductible_account_id
                    or move.journal_id.default_account_id
                ).id,
                'display_type': 'non_deductible_product_total',
                'name': _('private part'),
                'balance': non_deductible_base_total,
                'amount_currency': non_deductible_base_currency_total,
                'tax_ids': [Command.clear()],
                'sequence': max(move.line_ids.mapped('sequence')) + 1,
            })

        while to_create and to_delete:
            line_data = to_create.pop()
            line_id = to_delete.pop()
            self.env['account.move.line'].browse(line_id).write(line_data)
        if to_create:
            self.env['account.move.line'].create(to_create)
        if to_delete:
            self.env['account.move.line'].browse(to_delete).with_context(dynamic_unlink=True).unlink()