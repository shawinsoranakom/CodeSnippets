def _submit_to_myinvois(self):
        """
        Submit the documents in self to MyInvois.
        This action will re-generate a new XML file, in order to ensure that we always send an up-to-date version.
        """
        # Make sure that all documents in self have a file ready to be sent.
        self.action_generate_xml_file()

        # Submit the documents to the API
        errors = self._myinvois_submit_documents({
            document: {
                'name': document.name,
                'xml': base64.b64decode(document.myinvois_file).decode('utf-8'),
            } for document in self
        })

        # When sending an individual document, we can raise once we are sure we logged the errors.
        if len(self) == 1 and errors:
            if self._can_commit():
                self.env.cr.commit()  # Save the error logged in the chatter.
            raise UserError(errors[self.id]['plain_text_error'])

        # Try and get the status, up to three time, stopping if all documents have a status already.
        for _i in range(3):
            self._myinvois_submission_statuses_update()
            if not any(document.myinvois_state == 'in_progress' for document in self):
                break
            if self._can_commit():  # avoid the sleep in tests.
                time.sleep(1)