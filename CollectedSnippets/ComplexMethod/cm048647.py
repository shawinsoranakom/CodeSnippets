def _compute_abnormal_warnings(self):
        """Assign warning fields based on historical data.

        The last invoices (between 10 and 30) are used to compute the normal distribution.
        If the amount or days between invoices of the current invoice falls outside of the boundaries
        of the Bell curve, we warn the user.
        """
        if self.env.context.get('disable_abnormal_invoice_detection'):
            draft_invoices = self.browse()
        else:
            draft_invoices = self.filtered(lambda m:
                m.is_purchase_document()
                and m.state == 'draft'
                and m.amount_total
                and not (m.partner_id.ignore_abnormal_invoice_date and m.partner_id.ignore_abnormal_invoice_amount)
            )
        other_moves = self - draft_invoices
        other_moves.abnormal_amount_warning = False
        other_moves.abnormal_date_warning = False
        if not draft_invoices:
            return
        draft_invoices.flush_recordset(['invoice_date', 'date', 'amount_total', 'partner_id', 'move_type', 'company_id'])
        today = fields.Date.context_today(self)
        self.env.cr.execute("""
            WITH previous_invoices AS (
                  SELECT this.id,
                         other.invoice_date,
                         other.amount_total,
                         LAG(other.invoice_date) OVER invoice - other.invoice_date AS date_diff
                    FROM account_move this
                    JOIN account_move other USING (partner_id, move_type, company_id, currency_id)
                   WHERE other.state = 'posted'
                     AND other.invoice_date <= COALESCE(this.invoice_date, this.date, %(today)s)
                     AND this.id = ANY(%(move_ids)s)
                     AND this.id != other.id
                  WINDOW invoice AS (PARTITION BY this.id ORDER BY other.invoice_date DESC)
            ), stats AS (
                  SELECT id,
                         MAX(invoice_date)          OVER invoice AS last_invoice_date,
                         AVG(date_diff)             OVER invoice AS date_diff_mean,
                         STDDEV_SAMP(date_diff)     OVER invoice AS date_diff_deviation,
                         AVG(amount_total)          OVER invoice AS amount_mean,
                         STDDEV_SAMP(amount_total)  OVER invoice AS amount_deviation,
                         ROW_NUMBER()               OVER invoice AS row_number
                    FROM previous_invoices
                  WINDOW invoice AS (PARTITION BY id ORDER BY invoice_date DESC)
            )
              SELECT id, last_invoice_date, date_diff_mean, date_diff_deviation, amount_mean, amount_deviation
                FROM stats
               WHERE row_number BETWEEN 10 AND 30
            ORDER BY row_number ASC
        """, {
            'today': today,
            'move_ids': draft_invoices.ids,
        })
        result = {invoice: vals for invoice, *vals in self.env.cr.fetchall()}
        for move in draft_invoices:
            invoice_date = move.invoice_date or today
            (
                last_invoice_date, date_diff_mean, date_diff_deviation,
                amount_mean, amount_deviation,
            ) = result.get(move._origin.id, (invoice_date, 0, 10000000000, 0, 10000000000))

            if date_diff_mean > 25:
                # Correct for varying days per month and leap years
                # If we have a recurring invoice every month, the mean will be ~30.5 days, and the deviation ~1 day.
                # We need to add some wiggle room for the month of February otherwise it will trigger because 28 days is outside of the range
                date_diff_deviation += 1

            wiggle_room_date = 2 * date_diff_deviation
            move.abnormal_date_warning = (
                not move.partner_id.ignore_abnormal_invoice_date
                and (invoice_date - last_invoice_date).days < int(date_diff_mean - wiggle_room_date)
            ) and _(
                "The billing frequency for %(partner_name)s appears unusual. Based on your historical data, "
                "the expected next invoice date is not before %(expected_date)s (every %(mean)s (± %(wiggle)s) days).\n"
                "Please verify if this date is accurate.",
                partner_name=move.partner_id.display_name,
                expected_date=format_date(self.env, fields.Date.add(last_invoice_date, days=int(date_diff_mean - wiggle_room_date))),
                mean=int(date_diff_mean),
                wiggle=int(wiggle_room_date),
            )

            wiggle_room_amount = 2 * amount_deviation
            move.abnormal_amount_warning = (
                not move.partner_id.ignore_abnormal_invoice_amount
                and not (amount_mean - wiggle_room_amount <= move.amount_total <= amount_mean + wiggle_room_amount)
            ) and _(
                "The amount for %(partner_name)s appears unusual. Based on your historical data, the expected amount is %(mean)s (± %(wiggle)s).\n"
                "Please verify if this amount is accurate.",
                partner_name=move.partner_id.display_name,
                mean=move.currency_id.format(amount_mean),
                wiggle=move.currency_id.format(wiggle_room_amount),
            )