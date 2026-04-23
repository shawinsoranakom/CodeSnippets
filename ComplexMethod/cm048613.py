def _fetch_duplicate_reference(self, matching_states=('draft', 'in_process')):
        """ Retrieve move ids for possible duplicates of payments. Duplicates moves:
        - Have the same partner_id, amount and date as the payment
        - Are not reconciled
        - Represent a credit in the same account receivable or a debit in the same account payable as the payment, or
        - Represent a credit in outstanding receipts or debit in outstanding payments, so bank statement lines with an
         outstanding counterpart can be matched, or
        - Are in the suspense account
        """
        # Does not perform unnecessary check if partner_id or amount are not set, nor if payment is posted
        payments = self.filtered(lambda p: p.partner_id and p.amount and p.state != 'in_process')
        if not payments:
            return {}

        # Update tables involved in the query
        used_fields = ("company_id", "partner_id", "date", "state", "amount", 'payment_type')
        self.flush_model(used_fields)

        payment_table_and_alias = SQL("account_payment AS payment")
        if not self[0].id:  # if record is under creation/edition in UI, safely inject values in the query
            # Necessary since new record aren't searchable in the DB and record in edition aren't up to date yet
            values = {
                field_name: self._fields[field_name].convert_to_write(self[field_name], self) or None
                for field_name in used_fields
            }
            values["id"] = self._origin.id or 0
            # The amount total depends on the field line_ids and is calculated upon saving, we needed a way to get it even when the
            # invoices has not been saved yet.
            casted_values = SQL(', ').join(
                SQL("%s::%s", value, SQL.identifier(self._fields[field_name].column_type[0]))
                for field_name, value in values.items()
            )
            column_names = SQL(', ').join(SQL.identifier(field_name) for field_name in values)
            payment_table_and_alias = SQL("(VALUES (%s)) AS payment(%s)", casted_values, column_names)

        query = SQL(
            """
                SELECT payment.id AS payment_id,
                       ARRAY_AGG(DISTINCT duplicate_payment.id) AS duplicate_payment_ids
                  FROM %(payment_table_and_alias)s
                  JOIN account_payment AS duplicate_payment ON payment.id != duplicate_payment.id
                                                           AND payment.partner_id = duplicate_payment.partner_id
                                                           AND payment.company_id = duplicate_payment.company_id
                                                           AND payment.date = duplicate_payment.date
                                                           AND payment.payment_type = duplicate_payment.payment_type
                                                           AND payment.amount = duplicate_payment.amount
                                                           AND duplicate_payment.state IN %(matching_states)s
                 WHERE payment.id = ANY(%(payments)s)
              GROUP BY payment.id
            """,
            payment_table_and_alias=payment_table_and_alias,
            matching_states=tuple(matching_states),
            payments=payments.ids or [0],
        )

        return {
            payment_id: self.env['account.payment'].browse(duplicate_ids)
            for payment_id, duplicate_ids in self.env.execute_query(query)
        }