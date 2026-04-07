def _update_unget_history(self, num_bytes):
        """
        Update the unget history as a sanity check to see if we've pushed
        back the same number of bytes in one chunk. If we keep ungetting the
        same number of bytes many times (here, 50), we're mostly likely in an
        infinite loop of some sort. This is usually caused by a
        maliciously-malformed MIME request.
        """
        self._unget_history = [num_bytes] + self._unget_history[:49]
        number_equal = len(
            [
                current_number
                for current_number in self._unget_history
                if current_number == num_bytes
            ]
        )

        if number_equal > 40:
            raise SuspiciousMultipartForm(
                "The multipart parser got stuck, which shouldn't happen with"
                " normal uploaded files. Check for malicious upload activity;"
                " if there is none, report this to the Django developers."
            )