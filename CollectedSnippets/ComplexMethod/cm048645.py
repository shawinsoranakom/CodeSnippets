def _fetch_duplicate_reference(self, matching_states=('draft', 'posted')):
        moves = self.filtered(lambda m: m.is_sale_document() or m.is_purchase_document())

        if not moves:
            return {}

        used_fields = ("company_id", "partner_id", "commercial_partner_id", "ref", "move_type", "invoice_date", "state", "amount_total", "currency_id")

        self.env["account.move"].flush_model(used_fields)

        move_table_and_alias = SQL("account_move AS move")
        if not all(move.id for move in moves):  # check if record is under creation/edition in UI
            # New record aren't searchable in the DB and record in edition aren't up to date yet
            # Replace the table by safely injecting the values in the query
            all_values = []
            for move in moves:
                values = {
                    field_name: move._fields[field_name].convert_to_write(move[field_name], move) or None
                    for field_name in used_fields
                }
                values["id"] = move._origin.id or 0
                # The amount total depends on the field line_ids and is calculated upon saving,
                # we needed a way to get it even when the invoices has not been saved yet.
                values['amount_total'] = move.tax_totals.get('total_amount_currency', 0)
                casted_values = SQL(', ').join(
                    SQL("%s::%s", value, SQL.identifier(move._fields[field_name].column_type[0]))
                    for field_name, value in values.items()
                )
                all_values.append(SQL("(%s)", casted_values))
            column_names = SQL(', ').join(SQL.identifier(field_name) for field_name in used_fields + ("id",))
            move_table_and_alias = SQL("(VALUES %s) AS move(%s)", SQL(', ').join(all_values), column_names)

        to_query = []
        out_moves = moves.filtered(lambda m: m.move_type in ('out_invoice', 'out_refund'))
        if out_moves:
            out_moves_sql_condition = SQL("""
                move.move_type in ('out_invoice', 'out_refund')
                AND (
                   move.amount_total = duplicate_move.amount_total
                   AND move.invoice_date = duplicate_move.invoice_date
                )
            """)
            to_query.append((out_moves, out_moves_sql_condition))

        in_moves = moves.filtered(lambda m: m.move_type in ('in_invoice', 'in_refund'))
        if in_moves:
            in_moves_sql_condition = SQL("""
                move.move_type in ('in_invoice', 'in_refund')
                AND duplicate_move.move_type in ('in_invoice', 'in_refund')
                AND (
                   -- case 1: same ref and (no date or same year)
                     (
                         move.ref = duplicate_move.ref
                         AND (
                             move.invoice_date IS NULL
                             OR
                             duplicate_move.invoice_date IS NULL
                             OR
                             date_part('year', move.invoice_date) = date_part('year', duplicate_move.invoice_date)
                         )
                     )
                     -- case 2: different refs, same partner, amount and date
                     OR (
                            move.commercial_partner_id = duplicate_move.commercial_partner_id
                            AND move.amount_total = duplicate_move.amount_total
                            AND move.amount_total != 0.0
                            AND move.invoice_date = duplicate_move.invoice_date
                   )
                )
            """)
            to_query.append((in_moves, in_moves_sql_condition))

        result = []
        for moves, move_type_sql_condition in to_query:
            result.extend(self.env.execute_query(SQL("""
                SELECT move.id AS move_id,
                       array_agg(duplicate_move.id) AS duplicate_ids
                  FROM %(move_table_and_alias)s
                  JOIN account_move AS duplicate_move
                    ON move.company_id = duplicate_move.company_id
                   AND move.id != duplicate_move.id
                   AND duplicate_move.state IN %(matching_states)s
                   AND move.move_type = duplicate_move.move_type
                   AND move.currency_id = duplicate_move.currency_id
                   AND (
                           move.commercial_partner_id = duplicate_move.commercial_partner_id
                           OR (move.commercial_partner_id IS NULL AND duplicate_move.state = 'draft')
                       )
                   AND (%(move_type_sql_condition)s)
                 WHERE move.id IN %(moves)s
                 GROUP BY move.id
                """,
                matching_states=tuple(matching_states),
                moves=tuple(moves.ids or [0]),
                move_table_and_alias=move_table_and_alias,
                move_type_sql_condition=move_type_sql_condition,
            )))
        return {
            self.env['account.move'].browse(move_id): self.env['account.move'].browse(duplicate_ids)
            for move_id, duplicate_ids in result
        }