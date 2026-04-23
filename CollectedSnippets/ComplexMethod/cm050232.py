def _post_process(self):
        """ Override of `payment` to add account-specific logic to the post-processing.

        In particular, for confirmed transactions we write a message in the chatter with the payment
        and transaction references, post relevant fiscal documents, and create missing payments. For
        cancelled transactions, we cancel the payment.
        """
        super()._post_process()
        for tx in self.filtered(lambda t: t.state == 'done'):
            # Validate invoices automatically once the transaction is confirmed.
            self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()

            # Create and post missing payments.
            # As there is nothing to reconcile for validation transactions, no payment is created
            # for them. This is also true for validations with or without a validity check (transfer
            # of a small amount with immediate refund) because validation amounts are not included
            # in payouts. As the reconciliation is done in the child transactions for partial voids
            # and captures, no payment is created for their source transactions either.
            if (
                tx.operation != 'validation'
                and not tx.payment_id
                and not any(child.state in ['done', 'cancel'] for child in tx.child_transaction_ids)
            ):
                tx.with_company(tx.company_id)._create_payment()

            if tx.payment_id:
                message = _(
                    "The payment related to transaction %(ref)s has been posted: %(link)s",
                    ref=tx._get_html_link(),
                    link=tx.payment_id._get_html_link(),
                )
                tx._log_message_on_linked_documents(message)
        for tx in self.filtered(lambda t: t.state == 'cancel'):
            tx.payment_id.action_cancel()