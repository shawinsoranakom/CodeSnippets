def _get_received_message(self):
        """Return the message to log to state that the transaction has been processed.

        Note: `self.ensure_one()`

        :return: The message to log.
        :rtype: str
        """
        self.ensure_one()

        if self.operation == 'validation':
            return None  # Don't log anything as the token is not yet created.

        # Choose the message based on the transaction's state.
        msg_values = {
            'tx_label': 'refund' if self.operation == 'refund' else 'transaction',
            'ref': self._get_html_link(),
            'formatted_amount': self.currency_id.format(self.amount),
        }
        match self.state:
            case 'pending':
                received_message = _(
                    "The %(tx_label)s %(ref)s of %(formatted_amount)s is pending.",
                    **msg_values,
                )
            case 'authorized':
                received_message = _(
                    "The %(tx_label)s %(ref)s of %(formatted_amount)s has been authorized.",
                    **msg_values,
                )
            case 'done':
                received_message = _(
                    "The %(tx_label)s %(ref)s of %(formatted_amount)s has been confirmed.",
                    **msg_values,
                )
            case 'cancel':
                received_message = _(
                    "The %(tx_label)s %(ref)s of %(formatted_amount)s has been canceled.",
                    **msg_values,
                )
            case 'error':
                received_message = _(
                    "The %(tx_label)s %(ref)s of %(formatted_amount)s encountered an error.",
                    **msg_values,
                )
            case _:
                received_message = None

        # Append any state_message for cancel or error.
        if self.state in {'cancel', 'error'} and self.state_message:
            received_message += Markup("<br/>") + self.state_message

        return received_message