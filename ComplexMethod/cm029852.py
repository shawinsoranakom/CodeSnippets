def _get_tagged_response(self, tag, expect_bye=False):

        while 1:
            result = self.tagged_commands[tag]
            if result is not None:
                del self.tagged_commands[tag]
                return result

            if expect_bye:
                typ = 'BYE'
                bye = self.untagged_responses.pop(typ, None)
                if bye is not None:
                    # Server replies to the "LOGOUT" command with "BYE"
                    return (typ, bye)

            # If we've seen a BYE at this point, the socket will be
            # closed, so report the BYE now.
            self._check_bye()

            # Some have reported "unexpected response" exceptions.
            # Note that ignoring them here causes loops.
            # Instead, send me details of the unexpected response and
            # I'll update the code in '_get_response()'.

            try:
                self._get_response()
            except self.abort:
                if __debug__:
                    if self.debug >= 1:
                        self.print_log()
                raise