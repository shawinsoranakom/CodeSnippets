def _sync_tax_lines(self, container):
        AccountTax = self.env['account.tax']
        fake_base_line = AccountTax._prepare_base_line_for_taxes_computation(None)

        def get_base_lines(move):
            return move.line_ids.filtered(lambda line: line.display_type in ('product', 'epd', 'rounding', 'cogs', 'non_deductible_product'))

        def get_tax_lines(move):
            return move.line_ids.filtered('tax_repartition_line_id')

        def get_value(record, field):
            return record._fields[field].convert_to_write(record[field], record)

        def get_tax_line_tracked_fields(line):
            return ('amount_currency', 'balance', 'analytic_distribution')

        def get_base_line_tracked_fields(line):
            grouping_key = AccountTax._prepare_base_line_grouping_key(fake_base_line)
            if line.move_id.is_invoice(include_receipts=True):
                extra_fields = ['price_unit', 'quantity', 'discount']
            else:
                extra_fields = ['amount_currency']
            return list(grouping_key.keys()) + extra_fields

        def field_has_changed(values, record, field):
            return get_value(record, field) != values.get(record, {}).get(field)

        def get_changed_lines(values, records, fields=None):
            return (
                record
                for record in records
                if record not in values
                or any(field_has_changed(values, record, field) for field in values[record] if not fields or field in fields)
            )

        def any_field_has_changed(values, records, fields=None):
            return any(record for record in get_changed_lines(values, records, fields))

        def is_write_needed(line, values):
            return any(
                self.env['account.move.line']._fields[fname].convert_to_write(line[fname], self) != values[fname]
                for fname in values
            )

        moves_values_before = {
            move: {
                field: get_value(move, field)
                for field in ('currency_id', 'partner_id', 'move_type', 'invoice_currency_rate', 'invoice_date')
            }
            for move in container['records']
            if move.state == 'draft'
        }
        base_lines_values_before = {
            move: {
                line: {
                    field: get_value(line, field)
                    for field in get_base_line_tracked_fields(line)
                }
                for line in get_base_lines(move)
            }
            for move in container['records']
        }
        tax_lines_values_before = {
            move: {
                line: {
                    field: get_value(line, field)
                    for field in get_tax_line_tracked_fields(line)
                }
                for line in get_tax_lines(move)
            }
            for move in container['records']
        }
        yield

        to_delete = []
        to_create = []
        for move in container['records']:
            if move.state != 'draft':
                continue

            tax_lines = get_tax_lines(move)
            base_lines = get_base_lines(move)
            move_tax_lines_values_before = tax_lines_values_before.get(move, {})
            move_base_lines_values_before = base_lines_values_before.get(move, {})
            if (
                move.is_invoice(include_receipts=True)
                and (
                    field_has_changed(moves_values_before, move, 'currency_id')
                    or field_has_changed(moves_values_before, move, 'move_type')
                )
            ):
                # Changing the type of an invoice using 'switch to refund' feature or just changing the currency.
                round_from_tax_lines = False
            elif any(line not in base_lines for line, values in move_base_lines_values_before.items() if values['tax_ids']):
                # Removed a base line affecting the taxes.
                round_from_tax_lines = any_field_has_changed(move_tax_lines_values_before, tax_lines)
            elif field_has_changed(moves_values_before, move, 'invoice_currency_rate') and not field_has_changed(moves_values_before, move, 'invoice_date'):
                # Changing the rate should preserve the tax amounts in foreign currency but reapply the currency rate.
                round_from_tax_lines = 'reapply_currency_rate'
            elif changed_lines := list(get_changed_lines(move_base_lines_values_before, base_lines)):
                # A base line has been modified.
                round_from_tax_lines = (
                    # The changed lines don't affect the taxes.
                    all(
                        not line.tax_ids and not move_base_lines_values_before.get(line, {}).get('tax_ids')
                        for line in changed_lines
                    )
                    # Keep the tax lines amounts if an amount has been manually computed.
                    or (
                        list(move_tax_lines_values_before) != list(tax_lines)
                        or any(
                            self.env.is_protected(line._fields[fname], line)
                            for line in tax_lines
                            for fname in move_tax_lines_values_before[line]
                        )
                    )
                )

                # If the move has been created with all lines including the tax ones and the balance/amount_currency are provided on
                # base lines, we don't need to recompute anything.
                if (
                    round_from_tax_lines
                    and any(line[field] for line in changed_lines for field in ('amount_currency', 'balance'))
                ):
                    continue
            else:
                continue

            base_lines_values, tax_lines_values = move._get_rounded_base_and_tax_lines(round_from_tax_lines=round_from_tax_lines)
            AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines_values, move.company_id, include_caba_tags=move.always_tax_exigible)
            tax_results = AccountTax._prepare_tax_lines(base_lines_values, move.company_id, tax_lines=tax_lines_values)

            non_deductible_tax_line = move.line_ids.filtered(lambda line: line.display_type == 'non_deductible_tax')
            non_deductible_lines_values = [
                line_values
                for line_values in base_lines_values
                if line_values['special_type'] == 'non_deductible'
                and line_values['tax_ids']
            ]

            if not non_deductible_lines_values and non_deductible_tax_line:
                to_delete.append(non_deductible_tax_line.id)

            elif non_deductible_lines_values:
                non_deductible_tax_values = {
                    'tax_amount': 0.0,
                    'tax_amount_currency': 0.0,
                }
                for line_values in non_deductible_lines_values:
                    non_deductible_tax_values['tax_amount'] += -line_values['sign'] * (line_values['tax_details']['total_included'] - line_values['tax_details']['total_excluded'])
                    non_deductible_tax_values['tax_amount_currency'] += -line_values['sign'] * (line_values['tax_details']['total_included_currency'] - line_values['tax_details']['total_excluded_currency'])

                # Update the non-deductible tax lines values
                non_deductable_tax_line_values = {
                    'move_id': move.id,
                    'account_id': (
                        non_deductible_tax_line.account_id
                        or move.journal_id.non_deductible_account_id
                        or move.journal_id.default_account_id
                    ).id,
                    'display_type': 'non_deductible_tax',
                    'name': _('private part (taxes)'),
                    'balance': non_deductible_tax_values['tax_amount'],
                    'amount_currency': non_deductible_tax_values['tax_amount_currency'],
                    'sequence': max(move.line_ids.mapped('sequence')) + 1,
                }
                if non_deductible_tax_line:
                    tax_results['tax_lines_to_update'].append((
                        {'record': non_deductible_tax_line},
                        'unused_grouping_key',
                        {
                            'amount_currency': non_deductable_tax_line_values['amount_currency'],
                            'balance': non_deductable_tax_line_values['balance'],
                        }
                    ))
                else:
                    to_create.append(non_deductable_tax_line_values)

            for base_line, to_update in tax_results['base_lines_to_update']:
                line = base_line['record']
                if is_write_needed(line, to_update):
                    line.write(to_update)

            for tax_line_vals in tax_results['tax_lines_to_delete']:
                to_delete.append(tax_line_vals['record'].id)

            for tax_line_vals in tax_results['tax_lines_to_add']:
                to_create.append({
                    **tax_line_vals,
                    'display_type': 'tax',
                    'move_id': move.id,
                })

            for tax_line_vals, _grouping_key, to_update in tax_results['tax_lines_to_update']:
                line = tax_line_vals['record']
                if is_write_needed(line, to_update):
                    line.write(to_update)

        if to_delete:
            self.env['account.move.line'].browse(to_delete).with_context(dynamic_unlink=True).unlink()
        if to_create:
            self.env['account.move.line'].create(to_create)