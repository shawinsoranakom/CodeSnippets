def _myinvois_submission_statuses_update(self, with_commit=True):
        """
        Fetches and update the status of a group of documents.

        :param with_commit: If True, we will commit after retrieving the status if we can.
        """
        statuses = self._myinvois_get_submission_status()
        for submission_uid, results in statuses.items():
            records = self.browse(list(results['statuses'].keys()))

            if results['error']:
                message = self.env["account.move.send"]._format_error_html({
                    "error_title": self.env._("The status update failed with the following errors:"),
                    "errors": results['error'],
                })
                records._myinvois_log_message(bodies={document.id: message for document in self})
                if with_commit and self._can_commit():
                    self.env.cr.commit()
                continue

            for record, status in results['statuses'].items():
                # For valid documents, we always want to update the try time; it's pointless to fetch too often.
                if record.myinvois_state == 'valid' or status['status'] == 'valid':
                    record.myinvois_retry_at = fields.Datetime.now() + datetime.timedelta(hours=1)

                # If the status did not change, we do not need to do anything more.
                if record.myinvois_state == status['status']:
                    if with_commit and self._can_commit():
                        self.env.cr.commit()
                    continue

                # Invalid documents may not all have a reason, but we still want to log something.
                # We will have a reason when documents are cancelled/rejected though, and we want to log that too.
                message = None
                if status.get('reason') or status['status'] == 'invalid':
                    if status.get('reason'):
                        message = record.env._('The MyInvois platform returned a "%(status)s" status for this document for reason: %(reason)s', status=status['reason'], reason=status['reason'])
                    else:
                        message = record.env._('The MyInvois platform returned an "%(status)s" status for this document.', status=status['reason'])

                record._myinvois_set_state(status["status"], message)
                record._myinvois_set_validation_fields(status)

            if with_commit and self._can_commit():
                self.env.cr.commit()