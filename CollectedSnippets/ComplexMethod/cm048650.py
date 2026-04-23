def _inverse_amount_total(self):
        for move in self:
            if len(move.line_ids) != 2 or move.is_invoice(include_receipts=True):
                continue

            to_write = []

            amount_currency = abs(move.amount_total)
            balance = move.currency_id._convert(amount_currency, move.company_currency_id, move.company_id, move.invoice_date or move.date)

            for line in move.line_ids:
                if not line.currency_id.is_zero(balance - abs(line.balance)):
                    to_write.append((1, line.id, {
                        'debit': line.balance > 0.0 and balance or 0.0,
                        'credit': line.balance < 0.0 and balance or 0.0,
                        'amount_currency': line.balance > 0.0 and amount_currency or -amount_currency,
                    }))

            move.write({'line_ids': to_write})