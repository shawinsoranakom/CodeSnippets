def _is_section_applicable(section_alert, threshold_sums, invoice_currency_rate, lines):
            lines_total = sum(
                (line.price_total * invoice_currency_rate) if section_alert.consider_amount == 'total_amount' else line.balance
                for line in lines
            )
            if section_alert.is_aggregate_limit:
                aggregate_period_key = section_alert.consider_amount == 'total_amount' and 'price_total' or 'balance'
                aggregate_total = threshold_sums.get(section_alert.aggregate_period, {}).get(aggregate_period_key)
                if self.state == 'draft':
                    aggregate_total += lines_total
                if aggregate_total > section_alert.aggregate_limit:
                    return True
            return (
                section_alert.is_per_transaction_limit
                and lines_total > section_alert.per_transaction_limit
            )