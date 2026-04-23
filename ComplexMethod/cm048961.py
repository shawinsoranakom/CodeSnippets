def _myinvois_log_message(self, message=None, bodies=None):
        """
        Small helper to use when logging in the chatter to automatically broadcast the message to the invoice.

        Supports receiving a simple message string, or a dict of bodies targeted to self.
        """
        if message:
            self._message_log_batch(bodies={document.id: message for document in self})
            if self.invoice_ids:
                self.invoice_ids._message_log_batch(bodies={move.id: message for move in self.invoice_ids})

        documents_per_id = self.grouped('id')
        if bodies:
            self._message_log_batch(bodies=bodies)
            if self.invoice_ids:
                invoice_bodies = {}
                for document_id, message in bodies.items():
                    invoice_bodies.update({invoice.id: message for invoice in documents_per_id[document_id].invoice_ids})
                self.invoice_ids._message_log_batch(bodies=invoice_bodies)