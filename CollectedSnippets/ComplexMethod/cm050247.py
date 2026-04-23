def action_capture(self):
        self.ensure_one()

        remaining_amount_to_capture = self.amount_to_capture
        processed_txs_sudo = self.env['payment.transaction'].sudo()
        for source_tx in self.transaction_ids.filtered(lambda tx: tx.state == 'authorized'):
            partial_capture_child_txs = self.transaction_ids.child_transaction_ids.filtered(
                lambda tx: tx.source_transaction_id == source_tx and tx.state == 'done'
            )  # We can void all the remaining amount only at once => don't check cancel state.
            source_tx_remaining_amount = source_tx.currency_id.round(
                source_tx.amount - sum(partial_capture_child_txs.mapped('amount'))
            )
            if remaining_amount_to_capture:
                amount_to_capture = min(source_tx_remaining_amount, remaining_amount_to_capture)
                # In sudo mode because we need to be able to read on provider fields.
                processed_txs_sudo |= source_tx.sudo()._capture(
                    amount_to_capture=amount_to_capture
                )
                remaining_amount_to_capture -= amount_to_capture
                source_tx_remaining_amount -= amount_to_capture

            if source_tx_remaining_amount and self.void_remaining_amount:
                # The source tx isn't fully captured and the user wants to void the remaining.
                # In sudo mode because we need to be able to read on provider fields.
                processed_txs_sudo |= source_tx.sudo()._void(
                    amount_to_void=source_tx_remaining_amount
                )
            elif not remaining_amount_to_capture and not self.void_remaining_amount:
                # The amount to capture has been completely captured.
                break  # Skip the remaining transactions.
        return processed_txs_sudo._build_action_feedback_notification()